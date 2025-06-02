import logging
import requests
from datetime import date
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

GITHUB_PROVINCE_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json"

class CovidRegionData(models.Model):
    _name = 'covid.region.data'
    _description = 'COVID-19 Region Data'
    _order = 'total_cases desc, region_name asc'
    _rec_name = 'region_name'

    date = fields.Date(string="Date", required=True)
    region_name = fields.Char(string="Region Name", required=True)
    total_cases = fields.Integer(string="Total Cases", required=True)

    _sql_constraints = [
        ('date_region_uniq', 'unique(date, region_name)', 'Duplicate date and region is not allowed!'),
    ]

    def open_date_filter_wizard(self):
        return self.env.ref('odoo-covid.action_covid_date_filter_wizard').read()[0]

    def view_today_data(self):
        return self.env['covid.date.filter.wizard'].with_context(
            default_date_start=date.today(),
            default_date_end=date.today()
        ).create({}).apply_filter()