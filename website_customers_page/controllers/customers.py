import werkzeug.urls

from odoo import fields

from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.tools.translate import _


class MainCustomers(http.Controller):
    _references_per_page = 15

    @http.route([
        '/customers',
        '/customers/page/<int:page>',
        '/customers/country/<int:country_id>',
        '/customers/country/<country_name>-<int:country_id>',
        '/customers/country/<int:country_id>/page/<int:page>',
        '/customers/country/<country_name>-<int:country_id>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def customers(self, country_name=None, country_id=0, page=1, **post):
        # from wdb import set_trace
        # set_trace()
        limit = self._references_per_page
        offset = limit * (page - 1)
        Partner = request.env['res.partner']
        Country = request.env['res.country']
        post_name = post.get('search') or post.get('name', '')
        base_partner_domain = self.get_domain()
        current_country = None
        line_domain = base_partner_domain
        if post_name:
            line_domain += [('name', 'ilike', post_name)]

        # group by country, based on all customers (base domain)
        countries = Partner.sudo().read_group(
                        line_domain +
                        [("website_published", "=", True)],
                        ["id", "country_id"],
                        groupby="country_id",
                        orderby="country_id")
        countries_total = sum(country_dict['country_id_count'] for country_dict in countries)

        if country_id:
            line_domain += [('country_id', '=', country_id)]
            current_country = Country.browse(country_id).read(['id', 'name'])[0]
        
        countries.insert(0, {
            'country_id_count': countries_total,
            'country_id': (0, _("All Countries"))
        })
        
        partners = Partner.sudo().search(line_domain, offset, limit)
        count_partners = Partner.sudo().search_count(line_domain)

        base_url = '/customers'
        pager = request.website.pager(
                                    url=base_url,
                                    total=count_partners,
                                    page=page,
                                    step=limit,
                                    scope=7,
                                    url_args=post)
        values = {
            'partners': partners,
            'countries': countries,
            'current_country': current_country and [current_country['id'], current_country['name']] or None,
            'current_country_id': current_country and current_country['id'] or 0,
            'post': post,
            'pager': pager,
            'search': "?%s" % werkzeug.url_encode(post),
        }
        # from wdb import set_trace
        # set_trace()
        return request.render("website_customers_page.customers", values)

    @http.route(['/customers/<partner_id>'],
                type='http', auth="public", website=True)
    def partners_detail(self, partner_id, **post):
        _, partner_id = unslug(partner_id)
        if partner_id:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if partner.exists() and partner.website_published:
                values = {}
                values['main_object'] = values['partner'] = partner
                return request.render("website_customers_page.partner", values)
        return self.customers(**post)

    def get_domain(self):
        base_domain = [
            ("website_published", "=", True),
            ("customer", "=", True),
            ("is_company", "=", True)
        ]
        return base_domain
