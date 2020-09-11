
# django imports
from django.core.paginator import EmptyPage
from django.core.mail import send_mail
from django.template.loader import render_to_string
from MusicProj.settings import EMAIL_HOST_USER
from rest_framework.exceptions import ValidationError


def responsedata(status,message,data={}):
    if status:
        return {
            "status":status,
            "message":message,
            "data": data
        }
    else:
        return {
            "status":status,
            "message":message,
        }


def paginate(data, paginator, pagenumber, total_pages=0):
    """
    This method to create the paginated results in list API views.
    """
    if int(pagenumber) > paginator.num_pages:
        raise ValidationError("Not enough pages", code=404)
    try:
        previous_page_number = paginator.page(pagenumber).previous_page_number()
    except EmptyPage:
        previous_page_number = None
    try:
        next_page_number = paginator.page(pagenumber).next_page_number()
    except EmptyPage:
        next_page_number = int(pagenumber) + 1 if int(pagenumber) < total_pages else None

    if paginator.page(pagenumber).has_next():
        is_next_page = paginator.page(pagenumber).has_next() 
    else:
       is_next_page =  True if next_page_number else False 

    return {'pagination': {
        'previous_page': previous_page_number,
        'is_previous_page': paginator.page(pagenumber).has_previous(),
        'next_page': next_page_number,
        'is_next_page': is_next_page,
        'start_index': paginator.page(pagenumber).start_index(),
        'end_index': paginator.page(pagenumber).end_index(),
        'total_entries': paginator.count,
        'total_pages': paginator.num_pages,
        'page': int(pagenumber)
    }, 'results': data}


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def send_mail_request(recipient, mail_txt, mail_html, subject, **kwargs):
    """
    This method create the mail and send it to recipient.
    :param recipient: receiver of mail
    :param subject: subject line of the mail
    :param body: body of the mail
    """
    FROM = EMAIL_HOST_USER
    TO = recipient if type(recipient) is list else [recipient]
    msg_text, msg_html = None, None

    mail_dict = { 
                'resource_url': kwargs.get("resource_url"),
                'resource_name': kwargs.get("resource_name"),
                'sender': kwargs.get("sender"),
                'artists': kwargs.get("artists")
                }
    msg_text = render_to_string(mail_txt, mail_dict)
    msg_html = render_to_string(mail_html, mail_dict)          
    send_mail(subject, msg_text, FROM, TO, html_message=msg_html, fail_silently=False)