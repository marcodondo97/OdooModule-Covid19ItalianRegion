from odoo import models, fields, exceptions, _
import requests
import logging
from datetime import timedelta, date

_logger = logging.getLogger(__name__)

GITHUB_PROVINCE_URL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-json/dpc-covid19-ita-province.json"
MIN_DATE = date(2020, 2, 24)  # February 24th, 2020

class CovidDateFilterWizard(models.TransientModel):
    _name = 'covid.date.filter.wizard'
    _description = 'Date Range Filter for COVID Data'

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)

    def _fetch_and_store_data_from_json(self, date_str, json_data):
        # Extracts data for the specified date and saves totals by region
        covid_data_model = self.env['covid.region.data']
        region_totals = {}

        for item in json_data:
            if item["data"].startswith(date_str):
                region = item.get("denominazione_regione")
                total = item.get("totale_casi", 0)
                if region:
                    region_totals[region] = region_totals.get(region, 0) + total

        count = 0
        for region, total in region_totals.items():
            try:
                covid_data_model.create({
                    'date': date_str,
                    'region_name': region,
                    'total_cases': total,
                })
                count += 1
            except exceptions.ValidationError:
                pass  # Ignore duplicates

        _logger.info(f"{count} regions loaded for {date_str}")
        return count > 0

    def _build_action(self, domain):
        # Returns the action to open the filtered view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered COVID Data',
            'res_model': 'covid.region.data',
            'view_mode': 'list,form',
            'domain': domain,
            'create': False,
            'context': {
                'search_disable_custom_filters': True,
                'search_bar_visible': False,
                'orderby': 'total_cases desc',
                'group_by': 'region_name',
            },
        }

    def apply_filter(self):
        # Applies the date filter and loads missing data if needed
        # Validations
        if (self.date_start and self.date_start < MIN_DATE) or (self.date_end and self.date_end < MIN_DATE):
            raise exceptions.UserError(_("Data is available only from February 24th, 2020."))

        if self.date_end < self.date_start:
            raise exceptions.UserError(_("End date cannot be earlier than start date."))

        # Prepare domain
        domain = [('date', '>=', self.date_start), ('date', '<=', self.date_end)]

        # Download and parse JSON data
        try:
            res = requests.get(GITHUB_PROVINCE_URL)
            res.raise_for_status()
            all_data = res.json()
            _logger.info("JSON data successfully downloaded")
        except Exception as e:
            _logger.warning(f"Error downloading data from GitHub: {e}")
            return self._build_action(domain)

        covid_data_model = self.env['covid.region.data']
        data_loaded = False
        current_date = self.date_start

        while current_date <= self.date_end:
            date_str = current_date.strftime('%Y-%m-%d')
            if not covid_data_model.search_count([('date', '=', date_str)]):
                if self._fetch_and_store_data_from_json(date_str, all_data):
                    data_loaded = True
            current_date += timedelta(days=1)

        # Notifications
        if data_loaded:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': _('COVID Data'),
                'message': _('New data loaded successfully!'),
                'sticky': False,
            })
        elif not covid_data_model.search_count(domain):
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': _('COVID Data'),
                'message': _('No data found for the selected date range.'),
                'sticky': False,
                'type': 'warning',
            })

        return self._build_action(domain)
