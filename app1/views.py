from twilio.rest import Client
from app1.keys import *
import fitz  # PyMuPDF
import os
import re
from django.shortcuts import render ,HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import UploadedPDF, ProcessedPage
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def format_phone_number(phone):
    """Formats phone number from '8325616819' to '(832)561-6819'."""
    return f"({phone[:3]}){phone[3:6]}-{phone[6:]}"
@csrf_exempt
def extract_phone_number_from_text(text):
    """Extracts the first phone number from text in (XXX)XXX-XXXX format."""
    phone_pattern = r"\(\d{3}\)\d{3}-\d{4}"
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None
@csrf_exempt
def upload_pdf(request):
    """Admin Uploads the Main PDF & Extracts Pages"""
    if request.method == "POST" and request.FILES.get("pdf_file"):
        pdf_file = request.FILES["pdf_file"]
        
        # Check if the same file already exists in the database
        if UploadedPDF.objects.filter(file=f"uploaded_pdfs/{pdf_file.name}").exists():
            return render(request, "upload_success.html", {"message": "❌ File already uploaded!"})

        # Save new file
        fs = FileSystemStorage()
        filename = fs.save(f"uploaded_pdfs/{pdf_file.name}", pdf_file)
        uploaded_pdf = UploadedPDF(file=filename)
        uploaded_pdf.save()

        pdf_path = os.path.join(settings.MEDIA_ROOT, filename)
        doc = fitz.open(pdf_path)

        # Process each page in the PDF
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            phone_number = extract_phone_number_from_text(text)

            if phone_number:
                save_dir = os.path.join(settings.MEDIA_ROOT, "processed_pdfs")
                os.makedirs(save_dir, exist_ok=True)

                output_pdf_path = os.path.join(save_dir, f"{phone_number}_page{page_num+1}.pdf")
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                new_doc.save(output_pdf_path)

                ProcessedPage.objects.create(
                    phone_number=phone_number,
                    pdf_file=f"processed_pdfs/{phone_number}_page{page_num+1}.pdf"
                )

        return render(request, "upload_success.html", {"message": "✅ PDF processed successfully!"})
    a=Searches.objects.last()
    return render(request, "upload.html",{"counter":a.count})

# def search_patient(request):
#     """Patient Searches for Their PDF"""
#     pdf_file = None
#     if request.method == "POST":
#         last_name = request.POST.get("last_name", "").upper()
#         birth_year = request.POST.get("birth_year", "")
#         cell_number = request.POST.get("cell_number", "")
#         formatted_cell_number = format_phone_number(cell_number)

#         pdf_record = ProcessedPage.objects.filter(phone_number=formatted_cell_number).all()
#         list =[]
#         if pdf_record:
#             for i in pdf_record:
#                 pdf_file = i.pdf_file.url
#                 list.append(pdf_file)
        
#     try:
#         return render(request, "search.html", {"pdf_file": list})
#     except:
#         return render(request, "search.html")
import fitz  # PyMuPDF
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
@csrf_exempt
def search_text_in_pdf(pdf_path, last_name, birth_year):
    """Checks if a PDF contains the last name and birth year (case-insensitive)."""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text("text").lower()
                if last_name.lower() in text and birth_year in text:
                    return True  # Found match
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return False  # No match found
@csrf_exempt
def search_patient(request):
    """Patient Searches for Their PDF"""
    pdf_files = []
    found_match = False 
     # Track if any PDF contains the last name & birth year
    # try:
    #     count=Searches.objects.last()
    #     count.count=count.count+1
    #     count.save()
    # except:
    #     count=Searches.objects.create(count=1)
    #     count.save()
    

    # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    # if x_forwarded_for:
    #     ip = x_forwarded_for.split(',')[0]  # Extract first IP if multiple exist
    #     print(f'ip from if {ip}')
        
    # else:
    #     ip = request.META.get('REMOTE_ADDR')  # Get direct IP
    #     print(f'ip from else {ip}')



    if request.method == "POST":
        last_name = request.POST.get("last_name", "").strip()
        birth_year = request.POST.get("birth_year", "").strip()
        cell_number = request.POST.get("cell_number", "").strip()

        if not last_name or not birth_year or not cell_number:
            return render(request, "search.html", {"error": "Please provide all search fields."})

        formatted_cell_number = format_phone_number(cell_number)
        pdf_records = ProcessedPage.objects.filter(phone_number=formatted_cell_number).all()

        # First, check if any PDF has the required info
        for record in pdf_records:
            pdf_path = record.pdf_file.path  
            if search_text_in_pdf(pdf_path, last_name, birth_year):
                found_match = True
                break  # No need to check further, we found at least one match

        # If we found a match in any PDF, return all PDFs
        if found_match:
            pdf_files = [record for record in pdf_records]
            try:
                count=Searches.objects.last()
                count.count=count.count+1
                count.save()
            except:
                count=Searches.objects.create(count=1)
                count.save()
            return render(request, "search.html", {"pdf_file": pdf_files,"name":last_name,"year":birth_year,"number":cell_number})
        else:
            try:
                count=Searches.objects.last()
                count.count=count.count+1
                count.save()
            except:
                count=Searches.objects.create(count=1)
                count.save()
            return render(request, "search.html", {"error": "No matching records found.","name":last_name,"year":birth_year,"number":cell_number})

    return render(request, "search.html")
@csrf_exempt
def home(request):
    return render(request,'base.html')
@csrf_exempt
def message(request):
    a = UploadedPDF.objects.all()
    print(len(a))
    return render(request,'message.html',{"data":a})

from patient_record.settings import *
@csrf_exempt
def message_view(request):
    if request.method == "POST":
        selected_items = request.POST.getlist("selected_items")
        print("Selected IDs:", selected_items)
        for j in selected_items:  # Print selected IDs in console
            a = UploadedPDF.objects.filter(file = j).last()
            file_name = a.file
            file_name = f"{MEDIA_ROOT}\{file_name}"
            print (file_name)
            # file_name=str(file_name)
            # file_name=file_name.split()
            extract_patient_info(file_name)
        # for i in range(10):
        #     # print(a.file)
        #     print(selected_items)
        # return extract_patient_info(a)
        return HttpResponse("Messages sent to Patients")

    return render(request, "message.html", {"data": "data"})

@csrf_exempt
def extract_patient_info(pdf_path):
    """
    Extracts patient details including Name, Phone, Date of Birth, Payment Due, and Rendering Physician.
    :param pdf_path: Path to the PDF file.
    :return: List of extracted patient records.
    """
    data = []  

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")  # Extract text from the page

            phone = None
            patient_name = None
            dob = None
            payment_due = None
            rendering_physician = None

            # Extract Phone Number (Format: (XXX)XXX-XXXX)
            phone_match = re.search(r"\(\d{3}\)\d{3}-\d{4}", text)
            if phone_match:
                phone = phone_match.group()

            # Extract Patient Name
            patient_match = re.search(r"Patient:\s*[A-Z0-9]+\s*([A-Z][A-Z\s.]+)", text)
            if patient_match:
                patient_name = patient_match.group(1).strip()
                if len(patient_name) > 1:
                    patient_name = patient_name[:-1]  # Remove last character
                    # print(patient_name)
            # Extract Date of Birth (Format: MM/DD/YYYY or MM-DD-YYYY)
            dob_match = re.search(r"Date of Birth:\s*(\d{2}/\d{2}/\d{4})", text)
            if dob_match:
                dob = dob_match.group(1)

            # Extract Payment Due (Format: Currency values like 1234.56)
            payment_match = re.search(r"\b\d+\.\d+\b", text)
            if payment_match:
                payment_due = payment_match.group()
                
            # Extract Rendering Physician
            physician_match = re.search(r"Chart Number:\s*([A-Z\s.]+)", text)
            if physician_match:
                rendering_physician = physician_match.group(1).strip()
                if len(rendering_physician) > 1:
                    rendering_physician = rendering_physician[:-1]  # Remove last character

            # Ensure all key details are present before adding to the list
            if patient_name and phone and dob and payment_due and rendering_physician:
                # print(f"Hello {patient_name} you total bil is {payment_due} for the doctor {rendering_physician} with birth date of {dob} and is its your cell number {phone}")
                # import keys
                # name = "Muazzam"

                client = Client(account_sid,aut_token)
                message = client.messages.create(
                    body = f"Hello {patient_name} your total bill is $ {payment_due} for the doctor {rendering_physician} click here to view your statement https://consistent-danyette-nmbcs-e33af721.koyeb.app/ ",
                    from_=twilio_number,
                    to=target_number

                )
                print(message.body)
                # data.append([patient_name, phone, dob, payment_due, rendering_physician])
    # return HttpResponse('done')
