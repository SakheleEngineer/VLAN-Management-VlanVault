"""
Author: Sakhele George Mndaweni
Created: 2026-01-29
"""
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import TagSerializer
from rest_framework.decorators import action
import uuid
from django.shortcuts import render, get_object_or_404
from tag_set.models import  TagRange
from .forms import TagForm
from rest_framework import filters
from .models import VlanActivity
from .serializers import VlanActivitySerializer
from tag_set.forms import TagRangeForm
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from taglib.tag_utility_library  import *
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import csv
from django.http import HttpResponse
from django.urls import reverse
from datetime import datetime
from django.http import HttpResponse
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib import enums
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from django.core.cache import cache

def get_posts():
    print("fetched", cache.get("external_posts"))

@method_decorator(login_required, name='dispatch')
class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    @action(
        detail=False,
        methods=['get'],
        url_path='list-view(?:/(?P<uuid_str>[^/.]+))?',
        url_name='list-view'
    )
    def list_by_range(self, request, uuid_str=None):
        
        rows = []
        uuid_obj = uuid.UUID(uuid_str)
        if uuid:
            tag_range = get_object_or_404(TagRange, uuid=uuid_obj)
            tags = Tag.objects.filter(vlan_range=tag_range).order_by('vlan')
            rangeForm = TagRangeForm(instance= tag_range)
            # Initialize the form with the default vlan_range
            form = TagForm(initial={'vlan_range': tag_range})

            prev = tag_range.vlan_start - 1

            for tag in tags:
                vlan = tag.vlan

                # Ignore duplicates or bad data
                if vlan <= prev:
                    continue

                # GAP of ONE OR MORE VLANs
                if vlan > prev + 1:
                    gap_start = prev + 1
                    gap_end = vlan - 1

                    rows.append({
                        "type": "free",
                        "start": gap_start,
                        "end": gap_end,
                        "count": gap_end - gap_start + 1,
                    })

                # CURRENT VLAN IS IN USE
                rows.append({
                    "type": "tag",
                    "obj": tag,
                })

                prev = vlan

            # GAP AFTER LAST TAG
            if prev < tag_range.vlan_end:
                gap_start = prev + 1
                gap_end = tag_range.vlan_end

                rows.append({
                    "type": "free",
                    "start": gap_start,
                    "end": gap_end,
                    "count": gap_end - gap_start + 1,
                })

        else:
            tag_range = None
            tags = Tag.objects.all().order_by('vlan') 

        return render(
            request,
            'tags.html',
            {
                'tag_range': tag_range,
                'tags':      tags,
                'rangeForm': rangeForm,
                'form':      form,
                'rows':      rows
            }
        )

    @action(detail=False, methods=["post"], url_path="auto-reserve")
    def upload_tag_reserve(self, request):
        range_uuid = request.POST.get("range_uuid")
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            return Response({
                "success": False,
                "error": "No CSV uploaded"
            })

        tag_range = get_object_or_404(TagRange, uuid=range_uuid)

        results = create_tags_from_csv(tag_range, csv_file)

        request.session["csv_audit_results"] = {
            "audit_list": [
                {
                    "vlan": item["vlan"],
                    "customer": getattr(item["tag"], "customer", ""),
                    "division": getattr(item["tag"], "division", ""),
                    "name": getattr(item["tag"], "name", ""),
                    "service": getattr(item["tag"], "service", ""),
                    "speed": getattr(item["tag"], "speed", ""),
                    "status": item["status"],
                }
                for item in results["audit_list"]
            ],
            "occupied": results.get("occupied", []),
            "errors": results.get("errors", [])
        }

        return Response({
            "success": True,
            "result_url": reverse("csv-audit-results")
        })


class GetTagDataAPIView(APIView):

    def get(self, request):
        service_id = request.GET.get("service_id")

        if not service_id:
            return Response(
                {"error": "service_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        print("Received service_id:", service_id)

        token = get_snow_session_token()
        data = get_snow_service_data(token, service_id)

        print("Data from SNOW:", data)

        if not data:
            return Response(
                {"error": "No data found from SNOW"},
                status=status.HTTP_404_NOT_FOUND
            )

        temp = data.get("sector", "")

        sector = f"Sector-{temp.split('-')[-1]}"  # "3"

        tag_like_json = {
            "vlan": 0,
            "division": 'CN',
            "customer":data.get("name", ""),
            "name": data.get("end_company_name", ""),
            "access_hs": data.get("access_hs", ""),
            "sector": sector,
            "usage": data.get("delevary_type", ""),
            "service": data.get("service", ""),
            "speed": data.get("speed", ""),
            "circ_no": data.get("circuit_id", ""),
            "service_id": data.get("service_id", ""),
            "comment": "Auto-generated from SNOW"

        }

        return Response(tag_like_json, status=status.HTTP_200_OK)




class VlanActivityViewSet(ModelViewSet):
    """
    Full CRUD for VLAN activities
    """
    queryset = VlanActivity.objects.all().order_by('-timestamp')
    serializer_class = VlanActivitySerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp', 'vlan_id', 'level']
    ordering = ['-timestamp']
    search_fields = ['message', 'level', 'vlan_id']


class VlanLogViewSet(viewsets.ModelViewSet):
    queryset = VlanActivity.objects.all().order_by('-id')
    serializer_class = VlanActivitySerializer
    permission_classes = []  # or IsAuthenticated

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        log = response.data

        # Broadcast to websocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "vlan_logs",
            {
                "type": "send_log",
                "log": log
            }
        )
        return response


def download_csv_audit(request):
    """
    Professional PDF Audit Report
    - Occupied VLAN section removed
    - Page numbers
    - Header/footer
    - Wrapped table text
    - Better spacing and alignment
    - Status highlighting
    """

    data = request.session.get("csv_audit_results", {})

    audit_list = data.get("audit_list", [])
    errors = data.get("errors", [])

    success_count = sum(
        1 for item in audit_list
        if str(item.get("status", "")).lower() == "success"
    )

    failed_count = len(audit_list) - success_count

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'attachment; filename="Tag_Audit_Report_{datetime.now():%Y%m%d_%H%M%S}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=55,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#16324F"),
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#16324F"),
        spaceAfter=8,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=table_cell_style,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    elements = []

    elements.append(
        Paragraph(
            "COMSOL NETWORKS",
            ParagraphStyle(
                "CompanyTitle",
                parent=styles["Heading1"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#16324F"),
            ),
        )
    )

    elements.append(
        Paragraph(
            "TAG AUTO-RESERVATION AUDIT REPORT",
            title_style,
        )
    )

    elements.append(Spacer(1, 10))

    info_data = [
        ["Generated", datetime.now().strftime("%d %B %Y %H:%M:%S")],
        ["Report Type", "TAG Auto Reservation Audit"],
        ["Records Processed", str(len(audit_list))],
    ]

    info_table = Table(
        info_data,
        colWidths=[130, 350],
    )

    info_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    elements.append(info_table)
    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            "Audit Summary",
            section_style,
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Records Processed", str(len(audit_list))],
        ["Successful Reservations", str(success_count)],
        ["Failed Reservations", str(failed_count)],
        ["Validation Errors", str(len(errors))],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[300, 150],
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F8FAFC")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    elements.append(summary_table)
    elements.append(Spacer(1, 18))

    elements.append(
        Paragraph(
            "Audit Results",
            section_style,
        )
    )

    audit_table_data = [[
        Paragraph("VLAN", table_header_style),
        Paragraph("Customer", table_header_style),
        Paragraph("Division", table_header_style),
        Paragraph("Name", table_header_style),
        Paragraph("Service", table_header_style),
        Paragraph("Speed", table_header_style),
        Paragraph("Status", table_header_style),
    ]]

    for item in audit_list:

        audit_table_data.append([
            Paragraph(str(item.get("vlan", "")), table_cell_style),
            Paragraph(str(item.get("customer", "")), table_cell_style),
            Paragraph(str(item.get("division", "")), table_cell_style),
            Paragraph(str(item.get("name", "")), table_cell_style),
            Paragraph(str(item.get("service", "")), table_cell_style),
            Paragraph(str(item.get("speed", "")), table_cell_style),
            Paragraph(str(item.get("status", "")), table_cell_style),
        ])

    audit_table = Table(
        audit_table_data,
        repeatRows=1,
        splitByRow=True,
        colWidths=[
            40,
            70,
            55,
            110,
            120,
            40,
            55,
        ],
    )

    audit_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324F")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C7CBD1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    for row_num, item in enumerate(audit_list, start=1):

        status = str(item.get("status", "")).lower()

        if status == "success":
            audit_style.add(
                "BACKGROUND",
                (6, row_num),
                (6, row_num),
                colors.HexColor("#D4EDDA"),
            )
        else:
            audit_style.add(
                "BACKGROUND",
                (6, row_num),
                (6, row_num),
                colors.HexColor("#F8D7DA"),
            )

    audit_table.setStyle(audit_style)

    elements.append(audit_table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Validation Errors",
            section_style,
        )
    )

    if errors:

        error_data = [[
            Paragraph("Name", table_header_style),
            Paragraph("Error", table_header_style),
        ]]

        for err in errors:

            error_data.append([
                Paragraph(
                    str(err.get("name", "")),
                    table_cell_style,
                ),
                Paragraph(
                    str(err.get("error", "")),
                    table_cell_style,
                ),
            ])

        error_table = Table(
            error_data,
            repeatRows=1,
            splitByRow=True,
            colWidths=[150, 350],
        )

        error_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                 colors.HexColor("#C62828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4,
                 colors.HexColor("#C7CBD1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#FFF5F5")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        elements.append(error_table)

    else:

        elements.append(
            Paragraph(
                "No validation errors found.",
                styles["Normal"],
            )
        )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "This report was generated automatically by the TAG Auto-Reservation Audit System.",
            styles["Italic"],
        )
    )

    def add_header_footer(canvas, doc):

        canvas.saveState()

        canvas.setFont("Helvetica-Bold", 10)

        canvas.drawString(
            20,
            A4[1] - 25,
            "COMSOL NETWORKS - TAG AUTO-RESERVATION AUDIT REPORT",
        )

        canvas.setFont("Helvetica", 8)

        canvas.drawRightString(
            A4[0] - 20,
            15,
            f"Page {canvas.getPageNumber()}",
        )

        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=add_header_footer,
        onLaterPages=add_header_footer,
    )

    return response




def csv_audit_results(request):
    context = request.session.get("csv_audit_results", {})

    return render(
        request,
        "tags_audit_details.html",
        context
    )