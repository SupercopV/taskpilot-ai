import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

INVOICES = [
    {
        "filename": "ACME_INV_1023.pdf",
        "company": "Acme Corp",
        "invoice_number": "ACME-1023",
        "date": "2026-08-10",
        "due_date": "2026-09-10",
        "amount": 32000,
        "currency": "INR",
        "items": [
            ("Cloud Infrastructure Audit & Advisory", "1", "INR 20,000", "INR 20,000"),
            ("Security Posture Assessment", "1", "INR 12,000", "INR 12,000"),
        ],
        "notes": "Paid via NEFT on 2026-08-25. Standard Net-30 payment terms.",
    },
    {
        "filename": "ACME_INV_1024.pdf",
        "company": "Acme Corp",
        "invoice_number": "ACME-1024",
        "date": "2026-10-01",
        "due_date": "2026-10-15",
        "amount": 48500,
        "currency": "INR",
        "items": [
            ("Autonomous AI Workflow Orchestration", "1", "INR 35,000", "INR 35,000"),
            ("Agent Memory & Evaluation Pipeline", "1", "INR 13,500", "INR 13,500"),
        ],
        "notes": "LATEST INVOICE for Q4 services. Due within 15 days. Bank account details enclosed.",
    },
    {
        "filename": "TECHCORP_INV_778.pdf",
        "company": "TechCorp Solutions",
        "invoice_number": "TC-778",
        "date": "2026-09-28",
        "due_date": "2026-10-28",
        "amount": 65000,
        "currency": "INR",
        "items": [
            ("Custom High-Throughput API Gateway", "1", "INR 50,000", "INR 50,000"),
            ("Production Load Testing & Profiling", "1", "INR 15,000", "INR 15,000"),
        ],
        "notes": "Net-30. Authorized by Technical Operations lead.",
    },
    {
        "filename": "GLOBEX_INV_341.pdf",
        "company": "Globex Corporation",
        "invoice_number": "GLX-341",
        "date": "2026-09-15",
        "due_date": "2026-10-15",
        "amount": 18000,
        "currency": "INR",
        "items": [
            ("Real-Time Data Pipeline Monitoring Support", "1", "INR 18,000", "INR 18,000"),
        ],
        "notes": "Monthly recurring platform maintenance retainer.",
    },
    {
        "filename": "ENTERPRISE_INV_902.pdf",
        "company": "Enterprise Global Systems",
        "invoice_number": "ENT-902",
        "date": "2026-10-02",
        "due_date": "2026-11-02",
        "amount": 125000,
        "currency": "INR",
        "items": [
            ("Enterprise LLM Cluster Provisioning & Deployment", "1", "INR 95,000", "INR 95,000"),
            ("Security Hardening & Multi-Tenant IAM Setup", "1", "INR 30,000", "INR 30,000"),
        ],
        "notes": "HIGH-VALUE INVOICE. Requires mandatory executive / finance approval before processing.",
    },
]

def build_pdf(inv_data, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, inv_data["filename"])
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        leading=14
    )
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#059669'),
        spaceAfter=12
    )

    elements = []
    elements.append(Paragraph(f"<b>TAX INVOICE: {inv_data['company']}</b>", header_style))
    elements.append(Paragraph(f"Invoice Number: <b>{inv_data['invoice_number']}</b> | Status: Unprocessed", meta_style))
    elements.append(Spacer(1, 15))

    details_data = [
        [Paragraph(f"<b>Billed To:</b><br/>TaskPilot Technologies Ltd.<br/>Cyber City, Gurugram, India", meta_style),
         Paragraph(f"<b>Invoice Date:</b> {inv_data['date']}<br/><b>Payment Due Date:</b> {inv_data['due_date']}<br/><b>Currency:</b> {inv_data['currency']}", meta_style)]
    ]
    details_table = Table(details_data, colWidths=[270, 250])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Line Item Breakdown</b>", title_style))
    table_data = [["Description", "Qty", "Unit Price", "Total Amount"]]
    for desc, qty, unit_price, total in inv_data["items"]:
        table_data.append([desc, qty, unit_price, total])
    table_data.append(["", "", "Total Due:", f"{inv_data['currency']} {inv_data['amount']:,}"])

    item_table = Table(table_data, colWidths=[260, 50, 100, 110])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#cbd5e1')),
        ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.HexColor('#059669')),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Notes & Payment Instructions:</b><br/>{inv_data['notes']}", meta_style))
    doc.build(elements)
    print(f"Generated: {filepath}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "invoices")
    for inv in INVOICES:
        build_pdf(inv, target_dir)
    print("All simulated company invoices generated successfully.")

if __name__ == "__main__":
    main()
