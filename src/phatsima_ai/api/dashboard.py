from html import escape
from typing import Any

from phatsima_ai.core.catalogue import MORENA_PHATSIMA_PROFILE


def render_dashboard_html(
    enquiries: list[dict[str, Any]],
    tickets: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    quotations: list[dict[str, Any]],
    audit_log: list[dict[str, Any]],
) -> str:
    open_tickets = [t for t in tickets if t["status"] == "open"]
    new_leads = [lead for lead in leads if lead["status"] == "new"]
    pending_quotes = [q for q in quotations if q["status"] == "pending_approval"]

    quote_rows = "".join(
        f"""
        <tr>
            <td><strong>#{q['id']}</strong></td>
            <td>{escape(str(q['customer_id']))}</td>
            <td><code>{escape(str(q['service_code']))}</code></td>
            <td><strong>R {int(q['draft_amount_zar']):,}</strong></td>
            <td><span class="badge badge-{escape(str(q['status']))}">{escape(str(q['status']))}</span></td>
            <td>{escape(str(q['approved_by'] or '—'))}</td>
            <td>
                {
                    f'''
                    <button class="btn btn-approve" onclick="decideQuote({q['id']}, 'approved')">Approve</button>
                    <button class="btn btn-reject" onclick="decideQuote({q['id']}, 'rejected')">Reject</button>
                    '''
                    if q["status"] == "pending_approval"
                    else '<span class="muted">Finalised</span>'
                }
            </td>
        </tr>
        """
        for q in quotations
    ) or '<tr><td colspan="7" class="muted">No quotations drafted yet.</td></tr>'

    ticket_rows = "".join(
        f"""
        <tr>
            <td><strong>#{t['id']}</strong></td>
            <td>{escape(str(t['customer_id']))}</td>
            <td><code>{escape(str(t['service_code']))}</code></td>
            <td>{escape(str(t['department']))}</td>
            <td><span class="badge badge-open">{escape(str(t['status']))}</span></td>
            <td class="muted">{escape(str(t['created_at'])[:19])}</td>
        </tr>
        """
        for t in tickets
    ) or '<tr><td colspan="6" class="muted">No support tickets open.</td></tr>'

    lead_rows = "".join(
        f"""
        <tr>
            <td><strong>#{lead['id']}</strong></td>
            <td>{escape(str(lead['customer_id']))}</td>
            <td><code>{escape(str(lead['service_code']))}</code></td>
            <td>{int(lead['qualification_score'])} / 100</td>
            <td><span class="badge badge-new">{escape(str(lead['status']))}</span></td>
            <td class="muted">{escape(str(lead['created_at'])[:19])}</td>
        </tr>
        """
        for lead in leads
    ) or '<tr><td colspan="6" class="muted">No active leads yet.</td></tr>'

    enquiry_rows = "".join(
        f"""
        <tr>
            <td><strong>#{e['id']}</strong></td>
            <td>{escape(str(e['customer_id']))}</td>
            <td>{escape(str(e['channel']))}</td>
            <td><strong>{escape(str(e['classification']))}</strong><br><span class="muted">{escape(str(e['service']))}</span></td>
            <td>{escape(str(e['message']))}</td>
        </tr>
        """
        for e in enquiries[:15]
    ) or '<tr><td colspan="5" class="muted">No enquiries logged yet.</td></tr>'

    audit_rows = "".join(
        f"""
        <tr>
            <td class="muted">#{a['id']}</td>
            <td><code>{escape(str(a['entity_type']))} #{a['entity_id']}</code></td>
            <td><strong>{escape(str(a['action']))}</strong></td>
            <td>{escape(str(a['actor']))}</td>
            <td class="muted">{escape(str(a['timestamp'])[:19])}Z</td>
        </tr>
        """
        for a in audit_log[:20]
    ) or '<tr><td colspan="5" class="muted">No audit events recorded.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(MORENA_PHATSIMA_PROFILE.name)} — Operations Console</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #22c55e;
      --amber: #f59e0b;
      --red: #ef4444;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      background: #020617;
      border-bottom: 1px solid var(--border);
      padding: 1rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
    }}
    header h1 {{ margin: 0; font-size: 1.2rem; letter-spacing: 0.02em; }}
    header small {{ color: var(--muted); display: block; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 1.25rem; }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.25rem;
    }}
    .kpi .label {{ color: var(--muted); font-size: 0.82rem; text-transform: uppercase; }}
    .kpi .value {{ font-size: 1.85rem; font-weight: 700; margin-top: 0.25rem; }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.1rem 1.25rem;
      margin-bottom: 1.25rem;
      overflow-x: auto;
    }}
    .panel h2 {{ margin: 0 0 0.85rem; font-size: 1.05rem; color: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.6rem 0.65rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }}
    .muted {{ color: var(--muted); font-size: 0.82rem; }}
    .badge {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .badge-pending_approval {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
    .badge-approved, .badge-open {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
    .badge-rejected {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .badge-new {{ background: rgba(56, 189, 248, 0.2); color: #38bdf8; }}
    .btn {{
      border: none;
      border-radius: 6px;
      padding: 0.35rem 0.7rem;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      margin-right: 0.35rem;
    }}
    .btn-approve {{ background: var(--green); color: #052e16; }}
    .btn-reject {{ background: var(--red); color: #fff; }}
    .btn-primary {{ background: var(--accent); color: #082f49; padding: 0.55rem 1rem; }}
    .form-grid {{
      display: grid;
      grid-template-columns: 180px 130px 1fr auto;
      gap: 0.6rem;
      align-items: center;
    }}
    @media (max-width: 760px) {{ .form-grid {{ grid-template-columns: 1fr; }} }}
    input, select {{
      background: #0f172a;
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.5rem 0.65rem;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{escape(MORENA_PHATSIMA_PROFILE.name)} — AI Operations Console</h1>
      <small>{escape(MORENA_PHATSIMA_PROFILE.base_location)} • WhatsApp {escape(MORENA_PHATSIMA_PROFILE.whatsapp_phone)}</small>
    </div>
    <div>
      <a href="/docs" style="color: var(--accent); text-decoration: none; font-size: 0.9rem;">API Docs (/docs) →</a>
    </div>
  </header>

  <main class="container">
    <section class="kpis">
      <div class="kpi"><div class="label">Total Enquiries</div><div class="value">{len(enquiries)}</div></div>
      <div class="kpi"><div class="label">Open Tickets</div><div class="value">{len(open_tickets)}</div></div>
      <div class="kpi"><div class="label">New Leads</div><div class="value">{len(new_leads)}</div></div>
      <div class="kpi"><div class="label">Pending Quotes</div><div class="value">{len(pending_quotes)}</div></div>
    </section>

    <section class="panel">
      <h2>Quick Intake Simulator (POST /enquiries)</h2>
      <form class="form-grid" onsubmit="submitEnquiry(event)">
        <input id="customer_id" type="text" placeholder="Customer ID" value="potch-client-01" required />
        <select id="channel">
          <option value="whatsapp">whatsapp</option>
          <option value="web">web</option>
          <option value="api">api</option>
        </select>
        <input id="message" type="text" placeholder="e.g. How much for a business website? or My Wi-Fi keeps dropping in Ikageng" required />
        <button class="btn btn-primary" type="submit">Run Triage</button>
      </form>
    </section>

    <section class="panel">
      <h2>Quotation Approval Queue (Human-in-the-Loop)</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Customer</th><th>Service</th><th>Draft ZAR</th><th>Status</th><th>Reviewer</th><th>Action</th></tr>
        </thead>
        <tbody>{quote_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Support &amp; Security Tickets</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Customer</th><th>Service</th><th>Department</th><th>Status</th><th>Created (UTC)</th></tr>
        </thead>
        <tbody>{ticket_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Sales, Training &amp; Advisory Leads</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Customer</th><th>Service</th><th>Score</th><th>Status</th><th>Created (UTC)</th></tr>
        </thead>
        <tbody>{lead_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Recent Enquiries</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Customer</th><th>Channel</th><th>Classification &amp; Service</th><th>Message</th></tr>
        </thead>
        <tbody>{enquiry_rows}</tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Immutable Audit Trail</h2>
      <table>
        <thead>
          <tr><th>#</th><th>Entity</th><th>Action</th><th>Actor</th><th>Timestamp</th></tr>
        </thead>
        <tbody>{audit_rows}</tbody>
      </table>
    </section>
  </main>

  <script>
    async function submitEnquiry(e) {{
      e.preventDefault();
      const payload = {{
        customer_id: document.getElementById('customer_id').value,
        channel: document.getElementById('channel').value,
        message: document.getElementById('message').value
      }};
      const res = await fetch('/enquiries', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      if (res.ok) {{
        window.location.reload();
      }} else {{
        alert('Error submitting enquiry: ' + res.status);
      }}
    }}

    async function decideQuote(id, decision) {{
      const reviewer = prompt('Confirm reviewer name for audit log:', 'Morena');
      if (!reviewer) return;
      const res = await fetch(`/quotations/${{id}}/decide`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ decision, reviewer }})
      }});
      if (res.ok) {{
        window.location.reload();
      }} else {{
        alert('Failed to update quotation: ' + res.status);
      }}
    }}
  </script>
</body>
</html>"""