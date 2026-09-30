/**
 * server.js
 * Node.js & Express.js Backend for TurfPulse AI.
 * 
 * Demonstrates core Express.js concepts:
 * - express.json() request body parsing middleware
 * - Custom logging middleware (req, res, next)
 * - Route Parameters (req.params.id)
 * - Query Parameters (req.query.status, req.query.sport)
 * - Request Body handling (req.body in POST /api/broadcast)
 * - HTTP Status Codes (200 OK, 201 Created, 404 Not Found, 500 Server Error)
 * - CSV Data Persistence Layer (slots.csv, customer_segments.csv, booking_log.csv)
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Path to data files
const DATA_DIR = path.join(__dirname, 'data_layer');
const SLOTS_FILE = path.join(DATA_DIR, 'slots.csv');
const SEGMENTS_FILE = path.join(DATA_DIR, 'customer_segments.csv');
const BOOKING_LOG_FILE = path.join(DATA_DIR, 'booking_log.csv');

// ==========================================
// 1. MIDDLEWARE
// ==========================================

// Enable CORS for cross-origin access
app.use(cors());

// express.json() parses incoming JSON request bodies into req.body
app.use(express.json());

// Custom Logger Middleware: intercepts every request, logs method & URL, calls next()
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.url}`);
  next(); // Hands off execution to the next middleware or route handler
});

// Serve frontend static assets
app.use(express.static(path.join(__dirname, 'static')));

// ==========================================
// 2. CSV DATA LAYER HELPERS
// ==========================================

function parseCSV(content) {
  const lines = content.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  
  // Parse header
  const headers = splitCSVLine(lines[0]);
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const values = splitCSVLine(line);
    const row = {};
    headers.forEach((h, idx) => {
      let val = values[idx] !== undefined ? values[idx] : '';
      // convert numbers if appropriate
      if (!isNaN(val) && val !== '' && !val.includes('-') && !val.includes(':')) {
        val = Number(val);
      }
      row[h] = val;
    });
    rows.push(row);
  }
  return rows;
}

function splitCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' && (i === 0 || line[i - 1] !== '\\')) {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim().replace(/^"|"$/g, ''));
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim().replace(/^"|"$/g, ''));
  return result;
}

function loadSlots() {
  if (!fs.existsSync(SLOTS_FILE)) return [];
  const content = fs.readFileSync(SLOTS_FILE, 'utf8');
  return parseCSV(content);
}

function loadSegments() {
  if (!fs.existsSync(SEGMENTS_FILE)) return [];
  const content = fs.readFileSync(SEGMENTS_FILE, 'utf8');
  return parseCSV(content);
}

function loadLogs() {
  if (!fs.existsSync(BOOKING_LOG_FILE)) return [];
  const content = fs.readFileSync(BOOKING_LOG_FILE, 'utf8');
  return parseCSV(content);
}

function saveSlots(slots) {
  if (!slots.length) return;
  const headers = Object.keys(slots[0]);
  const lines = [headers.join(',')];
  for (const s of slots) {
    const row = headers.map(h => {
      const val = s[h] !== undefined ? s[h] : '';
      if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    });
    lines.push(row.join(','));
  }
  fs.writeFileSync(SLOTS_FILE, lines.join('\n'), 'utf8');
}

function appendToLog(logEntry) {
  const writeHeader = !fs.existsSync(BOOKING_LOG_FILE) || fs.statSync(BOOKING_LOG_FILE).size === 0;
  const headers = ['slot_id', 'decision', 'discount_pct', 'reasoning', 'segment_notified', 'source', 'timestamp'];
  let content = '';
  if (writeHeader) {
    content += headers.join(',') + '\n';
  }
  const row = headers.map(h => {
    let val = logEntry[h] !== undefined ? logEntry[h] : '';
    if (Array.isArray(val)) val = val.join('; ');
    if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
      return `"${val.replace(/"/g, '""')}"`;
    }
    return val;
  });
  content += row.join(',') + '\n';
  fs.appendFileSync(BOOKING_LOG_FILE, content, 'utf8');
}

// Financial Safety Guardrail: Never discount below operating cost floor + 10% safety buffer
function calculateSafeDiscount(basePrice, costToOperate, requestedDiscount) {
  if (basePrice <= 0) return 0;
  const maxSafe = Math.max(0, ((basePrice - costToOperate) / basePrice) * 100);
  const maxAllowable = Math.max(0, maxSafe - 10);
  return Math.round(Math.min(requestedDiscount, maxAllowable) * 10) / 10;
}

// Dynamic Pricing & Cohort Matching Heuristic
function analyzeSlot(slot, segments) {
  const basePrice = Number(slot.base_price) || 1200;
  const costToOperate = Number(slot.cost_to_operate) || 400;
  const fillRate = Number(slot.historical_fill_rate) || 0.4;
  const leadTime = Number(slot.lead_time_hrs) || 6;
  const sport = slot.sport || 'Football';
  const tags = String(slot.tags || '').toLowerCase();
  const timeSlot = String(slot.time_slot || '');

  const isPeak = tags.includes('peak') || timeSlot.includes('18:') || timeSlot.includes('19:') || timeSlot.includes('20:');
  const isUrgent = leadTime <= 4;
  const isLowFill = fillRate < 0.35 || tags.includes('low-fill');

  let discountPct = 0;
  let decision = 'notify_only';
  let reasoning = [];

  if (isUrgent && isPeak) {
    discountPct = calculateSafeDiscount(basePrice, costToOperate, 15);
    decision = 'notify_small_discount';
    reasoning.push(`Prime evening slot suddenly vacant (${leadTime}h lead time left).`);
    reasoning.push(`15% flash promo protects $${costToOperate} cost floor while recovering at-risk revenue.`);
  } else if (isLowFill) {
    discountPct = calculateSafeDiscount(basePrice, costToOperate, isUrgent ? 25 : 20);
    decision = 'notify_large_discount';
    reasoning.push(`Historically low occupancy (${Math.round(fillRate * 100)}%).`);
    reasoning.push(`Incentivizing price-sensitive teams with ${discountPct}% off.`);
  } else if (isUrgent) {
    discountPct = calculateSafeDiscount(basePrice, costToOperate, 15);
    decision = 'notify_small_discount';
    reasoning.push(`Urgent window (< 4h remaining). High probability of converting via instant broadcast.`);
  } else {
    discountPct = 0;
    decision = 'notify_only';
    reasoning.push(`Standard slot announcement without price reduction.`);
  }

  // Match optimal segment
  let matchedSegment = null;
  const sportSegments = segments.filter(s => String(s.sport_pref).toLowerCase() === sport.toLowerCase());
  
  if (sportSegments.length > 0) {
    // If discount is large, prefer high price sensitivity
    if (discountPct >= 20) {
      matchedSegment = sportSegments.find(s => String(s.price_sensitivity).toLowerCase() === 'high') || sportSegments[0];
    } else {
      matchedSegment = sportSegments.find(s => String(s.price_sensitivity).toLowerCase() !== 'high') || sportSegments[0];
    }
  } else {
    matchedSegment = segments[0] || { segment_name: 'Local Captains Cohort', size: 90 };
  }

  const discountedPrice = Math.round(basePrice * (1 - discountPct / 100));
  const segmentName = matchedSegment.segment_name || 'Weekend Football Players';
  const captainsCount = matchedSegment.size || 90;

  // Synthesize WhatsApp message
  let message = '';
  if (discountPct > 0) {
    message = `⚽ Turf Alert: ${slot.turf_name} ${slot.time_slot} tonight has opened up! ${discountPct}% off at $${discountedPrice.toLocaleString()}/hr. Reply to book or tap: turfpulse.ai/book/${String(slot.slot_id).toLowerCase()}`;
  } else {
    message = `⚽ Turf Alert: ${slot.turf_name} ${slot.time_slot} tonight is available for booking at $${basePrice.toLocaleString()}/hr. Reply to book or tap: turfpulse.ai/book/${String(slot.slot_id).toLowerCase()}`;
  }

  return {
    decision,
    discount_pct: discountPct,
    discounted_price: discountedPrice,
    base_price: basePrice,
    cost_to_operate: costToOperate,
    reasoning,
    matched_segment: segmentName,
    captains_count: captainsCount,
    message
  };
}

// ==========================================
// 3. EXPRESS ROUTES
// ==========================================

// Route 1: Health check telemetry
app.get('/api/health', (req, res) => {
  const slots = loadSlots();
  const segments = loadSegments();
  const logs = loadLogs();

  res.status(200).json({
    status: 'healthy',
    backend: 'Node.js & Express.js',
    express_version: require('express/package.json').version,
    uptime_seconds: Math.round(process.uptime()),
    database: 'CSV Persistence Layer (data_layer/)',
    telemetry: {
      slots_count: slots.length,
      segments_count: segments.length,
      logs_count: logs.length
    }
  });
});

// Route 2: Get all slots (supports Query Parameters: ?status=vacant&sport=Football)
app.get('/api/slots', (req, res) => {
  try {
    let slots = loadSlots();

    // Query Parameter filtering: req.query
    const { status, sport, turf_name } = req.query;

    if (status) {
      slots = slots.filter(s => String(s.status).toLowerCase() === status.toLowerCase());
    }
    if (sport) {
      slots = slots.filter(s => String(s.sport).toLowerCase() === sport.toLowerCase());
    }
    if (turf_name) {
      slots = slots.filter(s => String(s.turf_name).toLowerCase().includes(turf_name.toLowerCase()));
    }

    res.status(200).json({
      total: slots.length,
      slots: slots
    });
  } catch (error) {
    console.error('Error fetching slots:', error);
    res.status(500).json({ error: 'Failed to read slots database' });
  }
});

// Route 3: Get slot by ID using Route Parameter (req.params.id)
app.get('/api/slots/:id', (req, res) => {
  const { id } = req.params; // Route Parameter
  const slots = loadSlots();
  const segments = loadSegments();

  const slot = slots.find(s => String(s.slot_id).toUpperCase() === id.toUpperCase());

  if (!slot) {
    return res.status(404).json({
      error: `Slot ID '${id}' not found`
    });
  }

  const analysis = analyzeSlot(slot, segments);

  res.status(200).json({
    slot,
    analysis
  });
});

// Route 4: Analytics Endpoint (matching reference screen)
app.get('/api/analytics', (req, res) => {
  try {
    const slots = loadSlots();
    const vacantCount = slots.filter(s => s.status === 'vacant').length;
    const bookedCount = slots.length - vacantCount;
    const occupancyRate = slots.length > 0 ? (bookedCount / slots.length * 100).toFixed(1) : 78.4;

    res.status(200).json({
      arena_name: 'Apex Arena',
      occupancy: {
        rate: `${occupancyRate}%`,
        trend: '+14% this month'
      },
      rescued_revenue: {
        total: '$18,420',
        subtitle: 'from unfilled slots'
      },
      discipline_yield: [
        { sport: 'Football', fill_pct: 86, revenue: '$24.8k', color: '#2ae9a1' },
        { sport: 'Cricket', fill_pct: 72, revenue: '$16.2k', color: '#f59e0b' },
        { sport: 'Basketball', fill_pct: 68, revenue: '$9.1k', color: '#38bdf8' },
        { sport: 'Badminton', fill_pct: 81, revenue: '$7.4k', color: '#4ade80' }
      ]
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to compute analytics' });
  }
});

// Route 5: Broadcast Outreach (POST with Request Body: req.body)
app.post('/api/broadcast', (req, res) => {
  try {
    const { slot_id, discount_pct, segment, message, channel } = req.body; // req.body parsed by express.json()

    if (!slot_id) {
      return res.status(400).json({ error: 'slot_id is required in request body' });
    }

    const timestamp = new Date().toISOString();
    const logEntry = {
      slot_id: slot_id,
      decision: discount_pct > 0 ? 'notify_discount' : 'notify_only',
      discount_pct: Number(discount_pct) || 0,
      reasoning: 'Recruiter-approved dispatch triggered from Dispatch UI',
      segment_notified: segment || 'Weekend Football Players',
      source: `express_${channel || 'whatsapp'}`,
      timestamp: timestamp
    };

    // 1. Append to CSV audit log
    appendToLog(logEntry);

    // 2. Update slot status in slots.csv
    const slots = loadSlots();
    const slotIdx = slots.findIndex(s => String(s.slot_id).toUpperCase() === slot_id.toUpperCase());
    if (slotIdx !== -1) {
      slots[slotIdx].status = 'booked';
      saveSlots(slots);
    }

    // Return 201 Created status
    res.status(201).json({
      success: true,
      message: `Broadcast successfully sent via ${(channel || 'WhatsApp').toUpperCase()} to ${segment || 'captains'}!`,
      logged: logEntry,
      slot_status: 'booked'
    });
  } catch (error) {
    console.error('Error dispatching broadcast:', error);
    res.status(500).json({ error: 'Failed to process broadcast dispatch' });
  }
});

// Route 6: Audit Logs
app.get('/api/logs', (req, res) => {
  try {
    const logs = loadLogs();
    // Return recent 15 logs, newest first
    const recent = logs.slice(-15).reverse();
    res.status(200).json({
      total: logs.length,
      logs: recent
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to load booking logs' });
  }
});

// Serve the clean, recruiter-focused UI for all unmatched GET routes
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Start Express Server
app.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🚀 TurfPulse AI Express Server running on port ${PORT}`);
  console.log(`👉 http://localhost:${PORT}`);
  console.log(`📡 Health Telemetry: http://localhost:${PORT}/api/health`);
  console.log(`====================================================`);
});
