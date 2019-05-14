import werkzeug.urls

from odoo import fields

from odoo import http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.tools.translate import _


class MainCustomers(http.Controller):
    _references_per_page = 20

    @http.route([
        '/customers',
    ], type='http', auth="public", website=True)
    def customers(self, page=1, **post):
        limit = self._references_per_page
        offset = limit * (page - 1)

        Partner = request.env['res.partner']
        base_partner_domain = [
            ("website_published", "=", True),
            ("customer", "=", True)
        ]
        
        line_domain = base_partner_domain
        partners = Partner.sudo().search(base_partner_domain, offset, limit)
        
        values = {
            'partners': partners,
            'post': post,
            'search': "?%s" % werkzeug.url_encode(post),
        }
        # from wdb import set_trace
        # set_trace()
        return request.render("website_customers.customers", values)
    
    @http.route(['/customers/<partner_id>'],
                type='http', auth="public", website=True)
    def partners_detail(self, partner_id, **post):
        _, partner_id = unslug(partner_id)
        if partner_id:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if partner.exists() and partner.website_published:
                values = {}
                values['main_object'] = values['partner'] = partner
                return request.render("website_customers.partner", values)
        return self.customers(**post)
