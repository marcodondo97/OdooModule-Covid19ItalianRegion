from odoo import http, exceptions
from odoo.http import request
import json
from datetime import datetime


class CovidDataAPI(http.Controller):
    @http.route('/api/covid', type='http', auth='public', methods=['GET'], csrf=False)
    def get_covid_data(self, **kwargs):
        """
        REST API endpoint to get COVID-19 region data with filtering and sorting capabilities.
        Uses the same logic as the date_filter_wizard to fetch and filter data.

        Query parameters:
        - date_start: Start date in YYYY-MM-DD format
        - date_end: End date in YYYY-MM-DD format
        - region: Region name to filter by
        - sort_by: Field to sort by (date, region_name, total_cases)
        - sort_order: Sort order (asc or desc, default is asc)

        Returns:
        - JSON array of COVID-19 region data records
        """
        # Parse date parameters
        date_start = kwargs.get('date_start')
        date_end = kwargs.get('date_end')

        if not date_start or not date_end:
            return json.dumps({'error': 'Both date_start and date_end parameters are required'})

        try:
            date_start_obj = datetime.strptime(date_start, '%Y-%m-%d').date()
            date_end_obj = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return json.dumps({'error': 'Invalid date format. Use YYYY-MM-DD format (e.g., 2020-02-24)'})

        # Create a date filter wizard instance
        wizard = request.env['covid.date.filter.wizard'].sudo().create({
            'date_start': date_start_obj,
            'date_end': date_end_obj
        })

        try:
            # Apply the filter (this will fetch and store data if needed)
            # This will validate dates and fetch data from GitHub if needed
            result = wizard.apply_filter()

            # Extract the domain from the result
            # The apply_filter method returns an action with a domain key
            domain = result.get('domain', [])

            # Add region filter if specified
            region = kwargs.get('region')
            if region:
                domain.append(('region_name', '=', region))

            # Determine sorting
            sort_by = kwargs.get('sort_by', 'date')
            if sort_by not in ['date', 'region_name', 'total_cases']:
                sort_by = 'date'  # Default to date if invalid field

            sort_order = kwargs.get('sort_order', 'asc')
            order = f"{sort_by} {sort_order}"

            # Fetch data using the domain from the wizard
            covid_data = request.env['covid.region.data'].sudo().search_read(
                domain=domain,
                fields=['date', 'region_name', 'total_cases'],
                order=order
            )

            # Convert date objects to string for JSON serialization
            for record in covid_data:
                if record.get('date'):
                    record['date'] = record['date'].strftime('%Y-%m-%d')

            # Return JSON response
            return json.dumps(covid_data)

        except exceptions.UserError as e:
            # Handle validation errors from the wizard
            return json.dumps({'error': str(e.name)})
        except Exception as e:
            # Handle other exceptions
            return json.dumps({'error': f'An unexpected error occurred: {str(e)}'})