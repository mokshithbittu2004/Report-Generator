import base64
from datetime import datetime
from typing import Optional
from jinja2 import Template
from app.core.logger import get_logger

logger = get_logger(__name__)

class ReportService:
    """Service for generating HTML reports."""
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Automation Execution Report</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
      /* Minimal Corporate Color Palette - 4 Colors */
      --primary: #1e40af;
      --primary-light: #3b82f6;
      --primary-dark: #1e3a8a;
      --success: #059669;
      --success-light: #d1fae5;
      --danger: #dc2626;
      --danger-light: #fee2e2;
      --info: #0369a1;
      --warning: #f59e0b;

      /* Premium Neutrals - Light Mode */
      --bg: #ffffff;
      --bg-secondary: #fafbfc;
      --bg-tertiary: #f3f4f6;
      --bg-hover: #f9fafb;
      
      /* Text Hierarchy */
      --text-primary: #0f172a;
      --text-secondary: #64748b;
      --text-tertiary: #94a3b8;
      
      /* Borders & Dividers */
      --border: #e2e8f0;
      --border-light: #f1f5f9;
      --border-subtle: #cbd5e1;

      /* Shadows - Premium Elevation */
      --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
      --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.04);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
      --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }


    /* Manual dark mode toggle */
    body.dark-mode {
      --bg: #0f172a;
      --bg-secondary: #1e293b;
      --bg-tertiary: #334155;
      --bg-hover: #1f2937;
      --text-primary: #f1f5f9;
      --text-secondary: #cbd5e1;
      --text-tertiary: #94a3b8;
      --border: #334155;
      --border-light: #475569;
      --border-subtle: #64748b;
      --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
      --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px 0 rgba(0, 0, 0, 0.3);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
      --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.3);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html {
      background: var(--bg);
      scroll-behavior: smooth;
    }

    body {
      background: var(--bg);
      color: var(--text-primary);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      font-size: 14px;
      line-height: 1.6;
      font-feature-settings: 'rlig' 1, 'calt' 1;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 48px 32px;
    display: block;
    }
    .main-content {
      display: flex;
      flex-direction: column;
    }

    /* Theme toggle button */
    .theme-toggle {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 44px;
      height: 44px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text-primary);
      cursor: pointer;
      font-size: 18px;
      transition: all 0.25s ease;
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--shadow-sm);
    }

    .theme-toggle:hover {
      background: var(--bg-hover);
      box-shadow: var(--shadow-md);
    }

    .theme-toggle:focus {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }

    /* ============================================
       HEADER & NAVIGATION
       ============================================ */

    .header {
      margin-bottom: 48px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 32px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 32px;
    }

    .header-left h1 {
      font-size: 32px;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 12px;
      color: var(--text-primary);
      line-height: 1.2;
    }

    .header-left > div {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .header-meta {
      display: flex;
      gap: 32px;
      font-size: 13px;
      color: var(--text-secondary);
      flex-wrap: wrap;
    }

    .meta-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
    }

    .meta-item strong {
      color: var(--text-primary);
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 11px 18px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text-primary);
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      white-space: nowrap;
      box-shadow: var(--shadow-xs);
    }

    .btn:hover {
      background: var(--bg-hover);
      border-color: var(--primary-light);
      color: var(--primary);
      box-shadow: var(--shadow-sm);
      transform: translateY(-1px);
    }

    .btn-primary {
      background: var(--primary);
      color: white;
      border-color: var(--primary);
      box-shadow: var(--shadow-sm);
    }

    .btn-primary:hover {
      background: var(--primary-dark);
      border-color: var(--primary-dark);
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }

    /* ============================================
       TABS & FILTERS
       ============================================ */

    .tabs-section {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
      gap: 32px;
    }

    .tabs {
      display: flex;
      gap: 32px;
    }

    .tab {
      position: relative;
      padding: 6px 0;
      font-weight: 500;
      font-size: 14px;
      color: var(--text-secondary);
      cursor: pointer;
      border: none;
      background: none;
      transition: color 0.25s ease;
    }

    .tab:hover {
      color: var(--text-primary);
    }

    .tab.active {
      color: var(--primary);
      font-weight: 600;
    }

    .tab.active::after {
      content: '';
      position: absolute;
      bottom: -20px;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--primary);
      border-radius: 2px 2px 0 0;
    }

    .filters {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-left: auto;
    }

    /* Base */
    .filter-btn {
      padding: 8px 14px;
      border-radius: 7px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text-secondary);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      white-space: nowrap;
    }

    .filter-btn:hover {
      border-color: var(--primary-light);
      background: var(--bg-hover);
    }

    /* PASSED (Green) */
    .filter-btn.passed:hover {
      background: rgba(5, 150, 105, 0.08);
      border-color: var(--success);
      color: var(--success);
    }

    .filter-btn.passed.active {
      background: var(--success);
      border-color: var(--success);
      color: white;
      box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
    }

    /* FAILED (Red) */
    .filter-btn.failed:hover {
      background: rgba(220, 38, 38, 0.08);
      border-color: var(--danger);
      color: var(--danger);
    }

    .filter-btn.failed.active {
      background: var(--danger);
      border-color: var(--danger);
      color: white;
      box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
    }

    /* ALL (Primary) */
    .filter-btn.active:not(.passed):not(.failed) {
      background: var(--primary);
      border-color: var(--primary);
      color: white;
      box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
    }

    /* ============================================
       STATS GRID - Premium Cards
       ============================================ */

    .stats-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
      margin-bottom: 40px;
    }

    .stat-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 28px;
      box-shadow: var(--shadow-xs);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .stat-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--primary);
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .stat-card:hover {
      border-color: var(--primary-light);
      box-shadow: var(--shadow-md);
      transform: translateY(-4px);
    }

    .stat-card:hover::before {
      opacity: 1;
    }

    .stat-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-tertiary);
      letter-spacing: 0.08em;
      margin-bottom: 16px;
      display: block;
    }

    .stat-value {
      font-size: 38px;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }

    .stat-unit {
      font-size: 12px;
      color: var(--text-secondary);
      font-weight: 500;
    }

    .stat-card.success .stat-value {
      color: var(--success);
    }

    .stat-card.danger .stat-value {
      color: var(--danger);
    }

    .stat-card.info .stat-value {
      color: var(--info);
    }

    /* ============================================
       PROGRESS & SUMMARY - Premium Layout
       ============================================ */

    .summary-section {
      display: grid;
      grid-template-columns: 1fr 260px;
      gap: 24px;
      margin-bottom: 40px;
      align-items: stretch;
    }

    .progress-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 28px;
      box-shadow: var(--shadow-xs);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .progress-card:hover {
      box-shadow: var(--shadow-sm);
      border-color: var(--border-subtle);
    }

    .progress-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;  /* NOT baseline */
      margin-bottom: 6px;   /* tighter */
    }

    .progress-title {
      font-weight: 700;
      font-size: 15px;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }

    .progress-value {
      font-size: 12px;
      font-weight: 700;
      color: var(--primary);
      background: rgba(30, 64, 175, 0.08);
      padding: 4px 10px;
      border-radius: 6px;
      line-height: 1;
    }

    .progress-bar {
      height: 8px;
      background: var(--bg-tertiary);
      border-radius: 999px;
      overflow: hidden;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--primary-light));
      border-radius: 999px;
      transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .progress-fill::after {
      content: '';
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      width: 8px;
      background: rgba(255, 255, 255, 0.4);
      border-radius: 999px;
    }

    .donut-card {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: var(--shadow-xs);
    }

    .donut-wrapper {
      position: relative;
      width: 160px;
      height: 160px;
      margin-bottom: 12px;
    }

    .donut-svg {
      transform: rotate(-90deg);
    }

    .donut-center {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
    }

    .donut-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .donut-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 4px;
    }

    /* ============================================
       TIMELINE - Premium Visualization
       ============================================ */

    .timeline-section {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 28px;
      margin-bottom: 40px;
      box-shadow: var(--shadow-xs);
      overflow-x: auto;
      transition: all 0.3s ease;
    }

    .timeline-section:hover {
      box-shadow: var(--shadow-sm);
      border-color: var(--border-subtle);
    }

    .timeline-track {
      display: flex;
      align-items: center;
      gap: 20px;
      min-width: max-content;
      padding: 8px 0;
    }

    .timeline-node {
      position: relative;
      text-align: center;
      cursor: pointer;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .timeline-dot {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      margin: 0 auto 10px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 0 0 4px rgba(255, 255, 255, 0);
      border: 2px solid white;
    }

    .timeline-dot.passed {
      background: var(--success);
    }

    .timeline-dot.failed {
      background: var(--danger);
    }

    .timeline-node:hover .timeline-dot {
      transform: scale(1.4);
      box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.05);
    }

    .timeline-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-secondary);
      max-width: 110px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      letter-spacing: 0.02em;
    }

    /* ============================================
       STEPS SECTION - Premium Expandable Cards
       ============================================ */

    .steps-container {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .step {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--shadow-xs);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .step:hover {
      box-shadow: var(--shadow-md);
      border-color: var(--primary-light);
    }

    .step.failed {
      border-left: 4px solid var(--danger);
    }

    .step.passed {
      border-left: 4px solid var(--success);
    }

    .step-header {
      padding: 20px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      gap: 16px;
      user-select: none;
      transition: background-color 0.25s ease;
    }

    .step-header:hover {
      background: var(--bg-hover);
    }

    .step.open .step-header {
      background: var(--bg-hover);
      border-bottom-color: var(--border);
    }

    .step-left {
      flex: 1;
      min-width: 0;
    }

    .step-title {
      font-weight: 700;
      font-size: 14px;
      color: var(--text-primary);
      margin-bottom: 6px;
      letter-spacing: -0.01em;
    }

    .step-subtitle {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 10px;
      font-weight: 500;
    }

    .duration-bar {
      height: 4px;
      background: var(--bg-tertiary);
      border-radius: 999px;
      overflow: hidden;
      max-width: 300px;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .duration-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--info));
      border-radius: 999px;
      transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .step-right {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 7px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      white-space: nowrap;
    }

    .badge.passed {
      background: rgba(5, 150, 105, 0.12);
      color: var(--success);
    }

    .badge.failed {
      background: rgba(220, 38, 38, 0.12);
      color: var(--danger);
    }

    .step-duration {
      font-size: 12px;
      color: var(--text-secondary);
      font-weight: 700;
      min-width: 70px;
      text-align: right;
      letter-spacing: 0.02em;
    }

    .step-toggle {
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-secondary);
      font-size: 14px;
      transition: all 0.25s ease;
      flex-shrink: 0;
    }

    .step.open .step-toggle {
      transform: rotate(180deg);
      color: var(--primary);
    }

    .step-body {
      display: none;
      border-top: 1px solid var(--border);
      padding: 24px;
      background: var(--bg-secondary);
      animation: slideDown 0.3s ease-out;
    }

    @keyframes slideDown {
      from {
        opacity: 0;
        transform: translateY(-8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .step.open .step-body {
      display: block;
    }

    .step-body-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }

    .block {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      transition: all 0.25s ease;
    }

    .block:hover {
      border-color: var(--border-subtle);
      box-shadow: var(--shadow-xs);
    }

    .block.ai-block {
      border-color: rgba(245, 158, 11, 0.25);
      background: rgba(245, 158, 11, 0.04);
    }

    .block.ai-block:hover {
      box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.3), var(--shadow-xs);
    }

    .block-label {
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--text-tertiary);
      letter-spacing: 0.08em;
      display: block;
      margin-bottom: 10px;
    }

    .block-content {
      font-size: 12px;
      color: var(--text-primary);
      line-height: 1.6;
      word-break: break-word;
    }

    .block-content a {
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
      transition: color 0.25s ease;
    }

    .block-content a:hover {
      color: var(--primary-dark);
      text-decoration: underline;
      text-decoration-thickness: 1.5px;
      text-underline-offset: 3px;
    }

    .screenshot-wrapper {
      margin-top: 16px;
    }

    .screenshot-label {
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--text-tertiary);
      letter-spacing: 0.08em;
      display: block;
      margin-bottom: 10px;
    }

    .screenshot-img {
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      border: 1px solid var(--border);
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: var(--shadow-xs);
    }

    .screenshot-img:hover {
      box-shadow: var(--shadow-lg);
      border-color: var(--primary-light);
      transform: translateY(-2px);
    }

    /* ============================================
       MODAL - Premium Overlay
       ============================================ */

    .modal {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.55);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 999;
      backdrop-filter: blur(8px);
      animation: fadeIn 0.25s ease-out;
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
        backdrop-filter: blur(0px);
      }
      to {
        opacity: 1;
        backdrop-filter: blur(8px);
      }
    }

    .modal.open {
      display: flex;
    }

    .modal-content {
      background: var(--bg);
      border-radius: 14px;
      max-width: 90vw;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-xl);
      animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px;
      border-bottom: 1px solid var(--border);
    }

    .modal-title {
      font-weight: 700;
      font-size: 17px;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }

    .modal-body {
      display: flex;
      gap: 16px;
      overflow: hidden;
      flex: 1;
      padding: 24px;
    }

    .canvas-wrapper {
      position: relative;
      overflow: auto;
      flex: 1;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: var(--bg-secondary);
    }

    #annotationCanvas {
      position: absolute;
      left: 0;
      top: 0;
      cursor: crosshair;
    }

    .modal-tools {
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-width: 110px;
    }

    .tool-btn {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 11px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 11px;
      font-weight: 700;
      transition: all 0.25s ease;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .tool-btn:hover {
      border-color: var(--primary);
      color: var(--primary);
      background: rgba(30, 64, 175, 0.04);
    }

    .tool-btn.active {
      background: var(--primary);
      color: white;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
    }

    /* ============================================
       PRINT / PDF STYLES
       ============================================ */

    @media print {
      body {
        background: white;
        color: black;
      }

      .header-actions,
      .controls,
      .filters {
        display: none !important;
      }

      .header {
        position: static;
        margin-bottom: 24px;
      }

      .step {
        page-break-inside: avoid;
        margin-bottom: 16px;
      }

      .step-body {
        display: block !important;
        background: white;
      }

      .tabs-section {
        display: none !important;
      }

      @page {
        margin: 20mm;
      }

      .container {
        padding: 0;
      }
    }

    /* ============================================
       RESPONSIVE DESIGN - Mobile First
       ============================================ */

    /* Script download actions */
    .script-actions {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .script-copy-btn {
      padding: 10px 16px;
      background: var(--primary);
      color: white;
      border: 1px solid var(--primary);
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      font-size: 12px;
      transition: all 0.25s ease;
    }

    .script-copy-btn:hover {
      background: var(--primary-dark);
      box-shadow: var(--shadow-md);
    }

    .script-copy-btn:focus {
      outline: 2px solid var(--primary-light);
      outline-offset: 2px;
    }

    .copy-feedback {
      font-size: 12px;
      color: var(--success);
      font-weight: 600;
      animation: fadeInOut 2s ease;
    }

    @keyframes fadeInOut {
      0%, 100% { opacity: 0; }
      10%, 90% { opacity: 1; }
    }

    /* Visual hierarchy improvements */
    .stat-card.danger .stat-value {
      color: var(--danger);
    }

    .step.failed {
      border-left-color: var(--danger);
      background: rgba(220, 38, 38, 0.02);
    }

    .step.passed {
      border-left-color: var(--success);
      background: rgba(5, 150, 105, 0.02);
    }

    @media (max-width: 1024px) {
      .container {
        padding: 40px 28px;
        grid-template-columns: 1fr;
      }

      .summary-section {
        grid-template-columns: 1fr;
      }

      .tabs {
        gap: 20px;
      }
    }

    @media (max-width: 768px) {
      .container {
        padding: 32px 20px;
      }

      .header {
        flex-direction: column;
        gap: 20px;
        border-bottom-width: 0;
        padding-bottom: 0;
        margin-bottom: 32px;
      }

      .header-left h1 {
        font-size: 28px;
      }

      .header-actions {
        width: 100%;
        flex-wrap: wrap;
      }

      .header-actions .btn {
        flex: 1;
        min-width: 140px;
      }

      .stats-container {
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
      }

      .stat-card {
        padding: 20px;
      }

      .stat-value {
        font-size: 32px;
      }

      .summary-section {
        grid-template-columns: 1fr;
        gap: 20px;
        
      }

      .tabs-section {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
        padding-bottom: 16px;
      }

      .filters {
        margin-left: 0;
      }

      .step-body-grid {
        grid-template-columns: 1fr;
      }

      .step-header {
        padding: 16px 18px;
        gap: 12px;
      }

      .step-right {
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
      }

      .step-duration {
        text-align: right;
      }

      .modal-body {
        flex-direction: column;
        gap: 12px;
      }

      .modal-tools {
        flex-direction: row;
        min-width: auto;
        justify-content: flex-end;
      }

      .tool-btn {
        flex: 1;
        min-width: 80px;
      }
    }

    @media (max-width: 480px) {
      .container {
        padding: 24px 16px;
        grid-template-columns: 1fr;
      }

      .theme-toggle {
        width: 40px;
        height: 40px;
        font-size: 16px;
      }

      .header-left h1 {
        font-size: 24px;
      }

      .header-meta {
        flex-direction: column;
        gap: 12px;
        font-size: 12px;
      }

      .stats-container {
        grid-template-columns: 1fr;
      }

      .stat-card {
        padding: 20px;
      }

      .stat-value {
        font-size: 28px;
      }

      .stat-label {
        font-size: 10px;
      }

      .tabs {
        gap: 16px;
        font-size: 13px;
      }

      .filters {
        gap: 6px;
      }

      .filter-btn {
        padding: 6px 10px;
        font-size: 11px;
      }

      .step-title {
        font-size: 13px;
      }

      .step-subtitle {
        font-size: 11px;
      }

      .badge {
        padding: 4px 10px;
        font-size: 10px;
      }

      .timeline-section {
        padding: 20px;
      }

      .donut-wrapper {
        width: 140px;
        height: 140px;
      }

      .donut-value {
        font-size: 24px;
      }

      .modal-content {
        max-width: 95vw;
        max-height: 95vh;
      }

      .modal-header {
        padding: 16px;
      }

      .modal-body {
        padding: 16px;
      }
    }

    /* Focus visible for keyboard navigation */
    button:focus-visible,
    a:focus-visible,
    .tab:focus-visible {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }

    /* Skip to main content link */
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    }

    .sr-only:focus {
      position: static;
      width: auto;
      height: auto;
      padding: inherit;
      margin: inherit;
      overflow: visible;
      clip: auto;
      white-space: normal;
      background: var(--primary);
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      z-index: 1000;
    }
  </style>
</head>

<body>

<!-- Skip to main content link -->
<a href="#main-content" class="sr-only">Skip to main content</a>

<!-- Theme Toggle Button -->
<button class="theme-toggle" onclick="toggleDarkMode()" title="Toggle dark mode" aria-label="Toggle dark mode (currently light mode)">🌙</button>

<div class="container">

  <main class="main-content" id="main-content">

  <!-- HEADER -->
  <div class="header" id="overview">
    <div class="header-left">
      <h1>Automation Execution Report</h1>
      <div style="margin-top:6px;font-size:14px;color:var(--text-secondary);">
        Test Case: <strong>{{ testcase_name }}</strong>
      </div>
      <div class="header-meta">
        <div class="meta-item">
          <span>Generated: {{ generated_at }}</span>
        </div>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn" onclick="downloadPDF()" aria-label="Download report as PDF">Download PDF</button>
    </div>
  </div>

  <!-- TABS & FILTERS -->
  <div class="tabs-section" id="stats" role="tablist" aria-label="Report sections">
    <div class="tabs">
    <button class="tab active" onclick="switchTab(this, 'overview')" role="tab" aria-selected="true">Overview</button>

    <button class="tab" onclick="switchTab(this, 'Execution_Video')" role="tab" aria-selected="false">Execution Video</button>

    <button class="tab" onclick="switchTab(this, 'Final_Script')" role="tab" aria-selected="false">Final Script</button>
    
    <button class="tab" onclick="switchTab(this, 'Repair_Report')">Repair Report</button>

    <button class="tab" onclick="switchTab(this, 'details')" role="tab" aria-selected="false">Details</button>

    <button class="tab" onclick="switchTab(this, 'logs')" role="tab" aria-selected="false">Execution Log</button>
    </div>
    <div class="filters" role="group" aria-label="Filter steps by status">
      <button class="filter-btn active" onclick="filterSteps('all', event)" aria-pressed="true">All Steps</button>
      <button class="filter-btn passed" onclick="filterSteps('passed', event)" aria-pressed="false">✓ Passed</button>
      <button class="filter-btn failed" onclick="filterSteps('failed', event)" aria-pressed="false">✕ Failed</button>

    </div>
  </div>

  <!-- STATS GRID -->
  <div class="stats-container">
    <div class="stat-card">
      <div class="stat-label">Total Steps</div>
      <div class="stat-value">{{ total_steps }}</div>
      <div class="stat-unit">execution steps</div>
    </div>
    <div class="stat-card success">
      <div class="stat-label">Passed Steps</div>
      <div class="stat-value">{{ passed_steps }}</div>
      <div class="stat-unit">completed successfully</div>
    </div>
    <div class="stat-card danger">
      <div class="stat-label">Failed Steps</div>
      <div class="stat-value">{{ failed_steps }}</div>
      <div class="stat-unit">encountered errors</div>
    </div>
    <div class="stat-card info">
      <div class="stat-label">Total Duration</div>
      <div class="stat-value">{{ total_duration }} s</div>
      <div class="stat-unit">execution time</div>
    </div>
  </div>

  <!-- SUMMARY SECTION -->
  <div class="summary-section">
    <div class="progress-card">
  <div class="progress-title-row">
    <div class="progress-title">Execution Progress</div>
    <div class="progress-value">{{ success_rate }}%</div>
  </div>

  <div class="progress-bar">
    <div class="progress-fill" style="width: {{ success_rate }}%"></div>
  </div>
</div>
    
    <div class="donut-card">
      <div class="donut-wrapper">
        <svg class="donut-svg" width="160" height="160">
          <circle cx="80" cy="80" r="60" stroke="var(--bg-tertiary)" stroke-width="12" fill="none"/>
          <circle
            cx="80"
            cy="80"
            r="60"
            stroke="var(--success)"
            stroke-width="12"
            fill="none"
            stroke-dasharray="{{ success_rate }} 100"
            pathLength="100"
          />
        </svg>
        <div class="donut-center">
          <div class="donut-value">{{ success_rate }}%</div>
          <div class="donut-label">Success Rate</div>
        </div>
      </div>
    </div>
  </div>

  <!-- TIMELINE -->
  <div class="timeline-section" id="timeline">
    <div class="timeline-track">
      {% for step in steps %}
        <div class="timeline-node" onclick="scrollToStep('{{ step.step_id }}')">
          <div class="timeline-dot {{ step.status }}"></div>
          <div class="timeline-label">Step {{ step.index }}</div>
        </div>
      {% endfor %}
    </div>
  </div>

  <!-- STEPS -->
  <div class="steps-container" id="steps">
    {% for step in steps %}
    <div class="step {{ step.status }}"
     data-step-id="{{ step.step_id }}"
     data-status="{{ step.status }}"
     id="{{ step.step_id }}">
      <div class="step-header" onclick="toggleStep(this)">
        <div class="step-left">
          <div class="step-title">Step {{ step.index }}</div>
          <div class="step-subtitle">{{ step.intent }}</div>
          <div class="duration-bar">
            <div class="duration-fill" data-duration="{{ step.duration }}"></div>
          </div>
        </div>
        <div class="step-right">
          <span class="badge {{ step.status }}">{{ step.status|upper }}</span>
          <span class="step-duration">{{ step.duration }}</span>
          <div class="step-toggle">▼</div>
        </div>
      </div>

      <div class="step-body">
        <div class="step-body-grid">
          <div class="block">
            <span class="block-label">Intent</span>
            <div class="block-content">{{ step.intent }}</div>
          </div>

          <div class="block ai-block">
            <span class="block-label">Step Summary</span>
            <div class="block-content">{{ step.ai_summary }}</div>
          </div>

          {% if step.url %}
          <div class="block">
            <span class="block-label">URL</span>
            <div class="block-content"><a href="{{ step.url }}" target="_blank">{{ step.url }}</a></div>
          </div>
          {% endif %}

          {% if step.screenshot %}
          <div class="block">
            <span class="block-label">Execution Timestamp</span>
            <div class="block-content">{{ step.timestamp | default('N/A') }} Seconds</div>
          </div>
          {% endif %}
        </div>

        {% if step.screenshot %}
        <div class="screenshot-wrapper">
          <span class="screenshot-label">Screenshot</span>
          <img class="screenshot-img" src="data:image/png;base64,{{ step.screenshot }}" onclick="openModal(this, 'Step {{ step.index }}')" />
        </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- EXECUTION VIDEO TAB -->
  <div class="tab-content" data-tab="Execution_Video" id="video" style="display:none;margin-bottom:40px;">
    {% if execution_video %}
    <div style="background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 28px; box-shadow: var(--shadow-xs);">
      <div style="font-weight:700;font-size:15px;margin-bottom:16px;color:var(--text-primary);">Execution Video</div>
      <video width="100%" controls style="border-radius:10px;border:1px solid var(--border);box-shadow:var(--shadow-sm);">
        <source src="data:video/mp4;base64,{{ execution_video }}" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    </div>
    {% else %}
    <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 40px; text-align: center;">
      <div style="color: var(--text-tertiary); font-size: 14px;">No execution video available</div>
    </div>
    {% endif %}
  </div>

  <!-- FINAL SCRIPT TAB -->
  <div class="tab-content" data-tab="Final_Script" id="script" style="display:none;margin-bottom:40px;">
    {% if final_script %}
    <div style="background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 28px; box-shadow: var(--shadow-xs);">
      <div style="font-weight:700;font-size:15px;margin-bottom:16px;color:var(--text-primary);">Final Executed Script</div>
      
      <div class="script-actions">
        <button class="script-copy-btn" onclick="copyScript()" aria-label="Copy script to clipboard">📋 Copy to Clipboard</button>
        <button class="script-copy-btn" onclick="downloadScript()" aria-label="Download script as Python file">⬇ Download .py</button>
      </div>

      <div id="scriptContainer" style="
          background: var(--bg-secondary);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 20px;
          overflow-x: auto;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          white-space: pre;
          line-height: 1.6;
          color: var(--text-primary);
      ">{{ final_script }}</div>
      <div id="copyFeedback" class="copy-feedback" style="display: none; margin-top: 12px;">✓ Copied to clipboard</div>
    </div>
    {% else %}
    <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 40px; text-align: center;">
      <div style="color: var(--text-tertiary); font-size: 14px;">No final script available</div>
    </div>
    {% endif %}
  </div>
  
  <!-- REPAIR REPORT TAB -->
  <div class="tab-content" data-tab="Repair_Report" id="repair" style="display:none;margin-bottom:40px;">
    {% if repair_report %}
    <div style="background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 28px; box-shadow: var(--shadow-xs);">
      <div style="font-weight:700;font-size:15px;margin-bottom:16px;color:var(--text-primary);">
        Repair Report
      </div>

      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px;">

  <div class="stat-card">
    <div class="stat-label">Execution ID</div>
    <div style="font-weight:600;font-size:14px">{{ repair_report.execution_id }}</div>
  </div>

  <div class="stat-card {% if repair_report.final_status == 'passed' %}success{% else %}danger{% endif %}">
    <div class="stat-label">Final Status</div>
    <div class="stat-value">{{ repair_report.final_status | upper }}</div>
  </div>

  <div class="stat-card info">
    <div class="stat-label">Iterations</div>
    <div class="stat-value">{{ repair_report.iterations }}</div>
  </div>

  <div class="stat-card">
    <div class="stat-label">Timestamp</div>
    <div style="font-size:13px">{{ repair_report.timestamp }}</div>
  </div>

</div>

<div style="margin-top:10px">

  <div style="font-weight:600;margin-bottom:10px">Repair Attempts</div>

  <table style="width:100%;border-collapse:collapse;font-size:13px">

    <thead>
      <tr style="background:var(--bg-secondary);border-bottom:1px solid var(--border)">
        <th style="text-align:left;padding:10px">Attempt</th>
        <th style="text-align:left;padding:10px">Outcome</th>
        <th style="text-align:left;padding:10px">Step ID</th>
        <th style="text-align:left;padding:10px">Timestamp</th>
      </tr>
    </thead>

    <tbody>
      {% for r in repair_report.repairs %}
      <tr style="border-bottom:1px solid var(--border-light)">
        <td style="padding:10px">{{ r.attempt }}</td>

        <td style="padding:10px">
          <span class="badge {% if r.outcome == 'patched' %}passed{% else %}failed{% endif %}">
            {{ r.outcome }}
          </span>
        </td>

        <td style="padding:10px;font-family:monospace">{{ r.step_id }}</td>

        <td style="padding:10px">
          {{ r.timestamp }}
        </td>
      </tr>
      {% endfor %}
    </tbody>

  </table>

</div>

    </div>
    {% else %}
    <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 40px; text-align: center;">
      <div style="color: var(--text-tertiary); font-size: 14px;">
        No repair report available
      </div>
    </div>
    {% endif %}
  </div>

  </main>
</div>

<!-- SCREENSHOT MODAL -->
<div id="imgModal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <div class="modal-title" id="modalTitle">Screenshot</div>
      <button class="btn" onclick="closeModal()">✕ Close</button>
    </div>

    <div class="modal-body">
      <div class="canvas-wrapper">
        <img id="modalImage" />
        <canvas id="annotationCanvas"></canvas>
      </div>

      <div class="modal-tools">
        <button class="tool-btn active" onclick="setTool('draw', event)">✏ Draw</button>
        <button class="tool-btn" onclick="setTool('rect', event)">▭ Box</button>
        <button class="tool-btn" onclick="setTool('text', event)">T Text</button>
        <button class="tool-btn" onclick="clearCanvas()">🗑 Clear</button>
      </div>
    </div>
  </div>
</div>

<script>
  let currentTool = 'draw';
  let drawing = false;
  let ctx, canvas;
  let startX, startY;


    // ============================
    // DARK MODE
    // ============================

    function toggleDarkMode() {
    const body = document.body;
    const btn = document.querySelector('.theme-toggle');

    const isDark = body.classList.toggle('dark-mode');

    localStorage.setItem('theme', isDark ? 'dark' : 'light');

    btn.textContent = isDark ? '☀️' : '🌙';
    btn.setAttribute(
        'aria-label',
        `Toggle dark mode (currently ${isDark ? 'dark' : 'light'} mode)`
    );
    }

  // Check dark mode preference on load
  function initDarkMode() {
    const savedDarkMode = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedDarkMode === 'true' || (savedDarkMode === null && prefersDark);
    
    if (shouldBeDark) {
      document.body.classList.add('dark-mode');
      document.querySelector('.theme-toggle').textContent = '☀️';
    }
  }

  // ========================================
  // SCRIPT COPY & DOWNLOAD
  // ========================================
  function copyScript() {
    const scriptContent = document.getElementById('scriptContainer').innerText;
    navigator.clipboard.writeText(scriptContent).then(() => {
      const feedback = document.getElementById('copyFeedback');
      feedback.style.display = 'block';
      setTimeout(() => {
        feedback.style.display = 'none';
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy:', err);
      alert('Failed to copy script. Please try again.');
    });
  }

  function downloadScript() {
    const scriptContent = document.getElementById('scriptContainer').innerText;
    const blob = new Blob([scriptContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'automation_script.py';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ========================================
  // KEYBOARD NAVIGATION
  // ========================================
  function setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Tab navigation through sections
      if (e.key === 'Tab') {
        // Default browser tab behavior
        return;
      }
      
      // Escape key for modal
      if (e.key === 'Escape') {
        closeModal();
      }

      // Ctrl/Cmd + C for copy in script section
      if ((e.ctrlKey || e.metaKey) && e.key === 'c' && document.getElementById('scriptContainer')) {
        const scriptEl = document.getElementById('scriptContainer');
        if (scriptEl.parentElement.parentElement.offsetParent !== null) {
          e.preventDefault();
          copyScript();
        }
      }

      // Arrow keys to navigate steps
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        const steps = Array.from(document.querySelectorAll('.step'));
        const activeStep = document.activeElement.closest('.step');
        if (!activeStep || steps.length === 0) return;

        const index = steps.indexOf(activeStep);
        let nextIndex = e.key === 'ArrowDown' ? index + 1 : index - 1;
        
        if (nextIndex >= 0 && nextIndex < steps.length) {
          steps[nextIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
          steps[nextIndex].focus();
        }
      }
    });
  }

  // Tab switching
  function switchTab(el, tab) {
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.remove('active');
      t.setAttribute('aria-selected', 'false');
    });
    el.classList.add('active');
    el.setAttribute('aria-selected', 'true');

    // Handle overview tab - hide tab-content, show timeline and steps
    if (tab === 'overview') {
      document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      document.querySelector('.timeline-section').style.display = 'block';
      document.querySelector('.steps-container').style.display = 'flex';
    } else {
      // Hide timeline and steps for other tabs
      document.querySelector('.timeline-section').style.display = 'none';
      document.querySelector('.steps-container').style.display = 'none';
      // Show the selected tab content
      document.querySelectorAll('.tab-content').forEach(c => {
        c.style.display = c.dataset.tab === tab ? 'block' : 'none';
      });
    }
  }


  // PDF download
  function downloadPDF() {
    window.print();
  }

  // Filter steps
  function filterSteps(status, ev) {
    document.querySelectorAll('.step').forEach(step => {
      step.style.display =
        status === 'all' || step.dataset.status === status ? 'block' : 'none';
    });

    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.classList.remove('active');
      btn.setAttribute('aria-pressed', 'false');
    });

    if (ev) {
      ev.target.classList.add('active');
      ev.target.setAttribute('aria-pressed', 'true');
    }
  }


  // Scroll to step
  function scrollToStep(stepId) {
    const el = document.getElementById(stepId);
    if (!el) return;

    // Ensure step is visible
    el.style.display = 'block';

    // Expand step
    el.classList.add('open');

    // Scroll
    el.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }



  // Toggle step open/close
  function toggleStep(el) {
    const step = el.closest('.step');
    if (step) step.classList.toggle('open');
  }


  // Normalize duration bars
  function normalizeDurationBars() {
    const fills = document.querySelectorAll('.duration-fill');

    const durations = Array.from(fills)
      .map(f => parseFloat(f.dataset.duration))
      .filter(d => !isNaN(d));

    if (!durations.length) return;

    const max = Math.max(...durations);

    fills.forEach(f => {
      const d = parseFloat(f.dataset.duration);
      f.style.width = isNaN(d) ? '0%' : ((d / max) * 100) + '%';
    });
  }

  // Modal functions
  function openModal(img, title) {
    const modal = document.getElementById('imgModal');
    const modalImg = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modalTitle');

    modal.classList.add('open');
    modalImg.src = img.src;
    modalTitle.innerText = title;

    setupCanvas();
  }

  function closeModal() {
    document.getElementById('imgModal').classList.remove('open');
  }

  function setTool(tool, ev) {
    currentTool = tool;
    document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
    if (ev) ev.target.classList.add('active');
  }


  function setupCanvas() {
    const img = document.getElementById('modalImage');
    canvas = document.getElementById('annotationCanvas');

    img.onload = () => {
      canvas.width = img.clientWidth;
      canvas.height = img.clientHeight;

      ctx = canvas.getContext('2d');
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;

      canvas.onmousedown = startDraw;
      canvas.onmousemove = drawMove;
      canvas.onmouseup = endDraw;
    };
  }


  function startDraw(e) {
    drawing = true;
    startX = e.offsetX;
    startY = e.offsetY;

    if (currentTool === 'draw') {
      ctx.beginPath();
      ctx.moveTo(startX, startY);
    }
  }

  function drawMove(e) {
    if (!drawing) return;

    if (currentTool === 'draw') {
      ctx.lineTo(e.offsetX, e.offsetY);
      ctx.stroke();
    }
  }

  function endDraw(e) {
    if (!drawing) return;
    drawing = false;

    if (currentTool === 'rect') {
      const w = e.offsetX - startX;
      const h = e.offsetY - startY;
      ctx.strokeRect(startX, startY, w, h);
    }

    if (currentTool === 'text') {
      const text = prompt('Enter annotation:');
      if (text) {
        ctx.fillStyle = '#ef4444';
        ctx.font = '16px sans-serif';
        ctx.fillText(text, startX, startY);
      }
    }
  }

  function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  // Print setup
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('.step').forEach(step => {
      step.classList.add('open');
    });
  });

  // Update sidebar on scroll
  window.addEventListener('scroll', updateActiveNavLink);

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    setupKeyboardNavigation();
    normalizeDurationBars();
    updateActiveNavLink();
  });
</script>

</body>
</html>

"""
    
    @staticmethod
    def generate_html(
        steps: list,
        overall_description: str,
        started_at: Optional[str],
        finished_at: Optional[str],
        final_script: str,
        execution_video: bytes,
        testcase_name: str,
        repair_report: Optional[dict] = None,
    ) -> str:
        try:
            # ---------------------------------------------------------
            # HARD GUARANTEE: steps must already be ordered
            # ---------------------------------------------------------
            indices = [s["summary"]["step_index"] for s in steps]
            if indices != sorted(indices):
                raise RuntimeError(f"Unordered steps received: {indices}")

            passed_count = sum(1 for s in steps if s["summary"]["status"] == "passed")
            failed_count = len(steps) - passed_count
            total_steps = len(steps)
            success_rate = round((passed_count / total_steps) * 100, 2) if total_steps else 0

            total_duration = sum(
                s["summary"].get("duration_sec") or 0
                for s in steps
            )

            steps_data = []

            for step in steps:
                summary = step["summary"]
                step_index = summary["step_index"]

                screenshot_b64 = ""
                if step.get("screenshot"):
                    screenshot_b64 = base64.b64encode(step["screenshot"]).decode()
                    
                video_b64 = ""
                if execution_video:
                    video_b64 = base64.b64encode(execution_video).decode()

                steps_data.append({
                    "step_id": f"step-{step_index}",
                    "index": step_index,
                    "name": summary["step_name"],
                    "intent": summary["intent"],
                    "status": summary["status"],
                    "duration": round(summary.get("duration_sec") or 0, 2),
                    "timestamp": step.get("execution_timestamp"),
                    "attempts": summary["attempts"],
                    "max_retries": summary["max_retries"],
                    "url": summary.get("url", ""),
                    "ai_summary": step.get("ai_summary", ""),
                    "screenshot": screenshot_b64,
                })

            template = Template(ReportService.HTML_TEMPLATE)
            return template.render(
                total_steps=total_steps,
                passed_steps=passed_count,
                failed_steps=failed_count,
                total_duration=round(total_duration, 2),
                overall_description=overall_description,
                steps=steps_data,
                generated_at=datetime.utcnow().isoformat(),
                success_rate=success_rate,
                final_script=final_script,
                execution_video=video_b64,
                testcase_name=testcase_name,
                repair_report=repair_report
            )

        except Exception as e:
            logger.error("Failed to generate HTML", extra={"error": str(e)})
            raise


