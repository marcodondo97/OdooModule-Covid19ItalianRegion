from odoo import http, exceptions
from odoo.http import request
import json
from datetime import datetime


class CovidDataAPI(http.Controller):
    @http.route('/api/covid', type='http', auth='public', methods=['GET'], csrf=False)
    def get_covid_data(self, **kwargs):
        date_start = kwargs.get('date_start')
        date_end = kwargs.get('date_end')

        if not date_start or not date_end:
            return json.dumps({'error': 'Both date_start and date_end parameters are required'})

        try:
            date_start_obj = datetime.strptime(date_start, '%Y-%m-%d').date()
            date_end_obj = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return json.dumps({'error': 'Invalid date format. Use YYYY-MM-DD format (e.g., 2020-02-24)'})

        try:
            wizard = request.env['covid.date.filter.wizard'].sudo().create({
                'date_start': date_start_obj,
                'date_end': date_end_obj
            })

            result = wizard.apply_filter()
            domain = result.get('domain', [])

            region = kwargs.get('region')
            if region:
                domain.append(('region_name', '=', region))

            sort_by = kwargs.get('sort_by', 'date')
            if sort_by not in ['date', 'region_name', 'total_cases']:
                sort_by = 'date'

            sort_order = kwargs.get('sort_order', 'asc')
            order = f"{sort_by} {sort_order}"

            covid_data = request.env['covid.region.data'].sudo().search_read(
                domain=domain,
                fields=['date', 'region_name', 'total_cases'],
                order=order
            )

            for record in covid_data:
                if record.get('date'):
                    record['date'] = record['date'].strftime('%Y-%m-%d')

            return json.dumps(covid_data)

        except exceptions.UserError as e:
            return json.dumps({'error': str(e.name)})
        except Exception as e:
            return json.dumps({'error': f'An unexpected error occurred: {str(e)}'})
