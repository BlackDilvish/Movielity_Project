from django.test import TestCase, Client
from datetime import date
import os
import json
from . import views
from . import models
from local_hist import tests as test_data
from datetime import date

class LocalizatorTestViews(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_mail_address(self):
        self.assertEqual(views.get_mail_address(), 
                        'covid-localizations@no-reply.com')

    def test_get_no_html(self):
        self.assertEqual(views.get_no_html(), 
                        'There is a chance that you had close contacts (smaller than 250m) in following places: \n')

    def test_get_error_validation(self):
        self.assertEqual(views.get_error_validation(), 
                        'Unfortunately sent file is not valid json. Please, check your data.')

    def test_get_error_format(self):
        self.assertEqual(views.get_error_format(), 
                        'It seems that your file is valid JSON, but it does not contain required content')

    def test_get_error_date(self):
        self.assertEqual(views.get_error_date(), 
                        'Selected dates are incorrect!')

    def test_check_for_label(self):
        self.assertEqual(views.check_for_label('nolabel'), False)

    def test_check_status_dates(self):
        self.assertEqual(views.check_status_dates(date.today(), date.today()), True)

    def test_get_mail_title(self):
        status = '[COVID LOCALIZATIONS] Important! Possible contact with infected person occured.' in views.get_mail_title()
        self.assertEqual(status, True)

    def test_home(self):
        response = self.client.get('/home')
        self.assertEqual(response.status_code, 200)

    def test_upload_get(self):
        response = self.client.get('/upload')
        self.assertEqual(response.status_code, 200)

    def test_upload_post(self):
        response = self.client.post(path='/upload', data={'file': ''})
        self.assertEqual(response.status_code, 200)

    def test_status_get(self):
        response = self.client.get('/status')
        self.assertEqual(response.status_code, 200)

    def test_status_post(self):
        response = self.client.post(path='/status', data={})
        self.assertEqual(response.status_code, 200)

    def test_instruction(self):
        response = self.client.get('/instruction')
        self.assertEqual(response.status_code, 200)

    def test_convert_date_empty(self):
        converted = views.convert_date('')
        self.assertEqual(converted, date.today())
        
    def test_convert_date(self):
        self.assertEqual(views.convert_date('2020-06-13'), date(2020, 6, 13))

    def test_validate_json(self):
        with open('test.json', 'w+') as f:
            f.write('{"key": 0}')
            validated = views.validate_json(f)

        os.remove('test.json')
        
        self.assertEqual(validated, False)
        
    def test_prepare_contacts(self):
        json = test_data.activity_full_data
        contacts = [{"location" : {"latitudeE7" : 0, "longitudeE7" : 1}}]
        views.prepare_contacts(contacts, json)
        self.assertEqual(len(contacts), 0)
        
    def test_execute_mail(self):
        contacts = [{"location" : {"latitudeE7" : 0, "longitudeE7" : 0}, 
        "user_loc" : {"latitude" : "2", "longitude" : "3"}, "infected_act" : "4", 
        "user_act" : "5", "near" : "6", "duration" : "7"}]
        views.execute_mail(contacts, "someone@gmail.com")
        self.assertEqual(contacts[0]["url"], 
                         "https://covidlocalizations.herokuapp.com/list-meetings/contact/0.0/0.0/2/3/4/5/6/7")
        
    def test_check_if_met_sick_person(self):
        self.assertFalse(views.check_if_met_sick_person({"timelineObjects" : {}}, "May2018", "someone", "someone@gmail.com"))

    def test_status_post_for_present_infected_person(self):
        response = self.client.post(path='/status', data=dict(save=True, infected_present="clicked",
                                                              start_date=date.today()))
        self.assertEqual(response.status_code, 200)

    def test_status_post_for_past_infected_person(self):
        response = self.client.post(path='/status', data=dict(save=True, infected_past="clicked",
                                                              start_date=date.today(), end_date=date.today()))
        self.assertEqual(response.status_code, 200)

    def test_status_post_for_not_infected(self):
        response = self.client.post(path='/status', data=dict(save=True, infected_present="not_clicked",
                                                              infected_past="not_clicked"))
        self.assertEqual(response.status_code, 200)

    def test_if_check_upload_returns_correct_str_for_test_user_which_already_uploaded(self):
        result_list = views.check_upload(name="asd")
        result_str = result_list[0]
        self.assertEqual(result_str, "You've already uploaded your localizations from:")

    def test_post_upload_with_file(self):
        file_name = os.path.join(os.path.dirname(__file__), 'example_file.json')
        logged_client = Client()
        logged_client.login(username='test_user', password='tester123')

        with open(file_name) as example_file:
            response = logged_client.post(path='/upload', data=dict(choose_month="june", choose_year=2020,
                                                                  uplfile=example_file))
        self.assertEqual(response.status_code, 200)


class LocalizatorTestModels(TestCase):
    def setUp(self):
        pass

    def test_localizations_data(self):
        loc_data = models.LocalizationsData()

        loc_data.name = 'name'
        loc_data.file_date = '01.01.2020'

        self.assertEqual(str(loc_data), 'name')
        self.assertEqual(loc_data.date(), str(date.today()))
        self.assertEqual(loc_data.json_file_date(), '01.01.2020')

    def test_health_status(self):
        health = models.HealthStatus()

        health.name = 'name'
        health.status = True
        health.start_date = date.today()
        health.end_date = date.today()

        self.assertEqual(str(health), 'name')
        self.assertEqual(health.covid_status(), True)
        self.assertEqual(health.covid_start_date(), str(date.today()))
        self.assertEqual(health.covid_end_date(), str(date.today()))

