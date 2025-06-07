import logging
import requests
from datetime import date
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)

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

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # Call the original 'read_group' method from the superclass to get the grouped data
        result = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        # Custom sorting of the grouped results based on specific grouping criteria
        if (groupby == ['region_name'] or
                groupby == 'region_name' or
                (isinstance(groupby, list) and 'region_name' in groupby)):
            # Sort the resulting grouped records in descending order by 'total_cases' value
            # Use 'get' with default 0 to handle cases where 'total_cases' key might be missing
            result.sort(key=lambda r: r.get('total_cases', 0), reverse=True)

        # Return the (potentially) sorted list of grouped records
        return result

    def view_today_data(self):
        # Reuses the wizard to show today's data
        return self.env['covid.date.filter.wizard'].with_context(
            default_date_start=date.today(),
            default_date_end=date.today()
        ).create({}).apply_filter()
