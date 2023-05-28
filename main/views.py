from rest_framework.views import APIView
from django.shortcuts import redirect
from rest_framework.response import Response
from django.views import View
import requests
import json
import http
import os
class GoogleCalendarInitView(APIView):
    def get(self, request):
        client_id = os.environ['client_id']
        redirect_uri = 'http://127.0.0.1:8000/rest/v1/calendar/redirect/'
        scope = 'https://www.googleapis.com/auth/calendar.readonly'
        auth_url = f'https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}'

        return redirect(auth_url)


class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        code = request.GET.get('code')

        access_token = self.exchange_code_for_token(code)
        events = self.fetch_calendar_events(access_token)

        return Response({'events': events})

    def exchange_code_for_token(self, code):
        token_endpoint = "https://oauth2.googleapis.com/token"
        client_id = os.environ['client_id']
        client_secret = os.environ['client_secret']
        redirect_uri = "http://127.0.0.1:8000/rest/v1/calendar/redirect/"

        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        response = requests.post(token_endpoint, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            return access_token
        else:
            return None

    def fetch_calendar_events(self, access_token):
        conn = http.client.HTTPSConnection("www.googleapis.com")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        conn.request("GET", "/calendar/v3/users/me/calendarList", headers=headers)
        response = conn.getresponse()

        if response.status == 200:
            data = response.read()
            calendar_list = json.loads(data)
            events = []
            for calendar in calendar_list['items']:
                calendar_id = calendar['id']
                try:
                    conn.request("GET", f"/calendar/v3/calendars/{calendar_id}/events", headers=headers)
                    response = conn.getresponse()
                    if response.status == 200:
                        data = response.read()
                        calendar_events = json.loads(data)
                        events.extend(calendar_events.get('items', []))
                    else:
                        print("Failed to retrieve calendar events.")
                except http.client.ResponseNotReady:
                    print("ResponseNotReady exception occurred.")
                    continue

            conn.close()

            return events
        else:
            print("Failed to retrieve calendar list.")

            conn.close()

            return None
