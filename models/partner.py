# -*- coding: utf-8 -*-
# © 2016 Tobias Zehntner
# © 2016 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Stored value for credit limit always in USD, will be displayed according
    # to the currency of the partner's default pricelist
    credit_limit = fields.Monetary(
        'Credit Limit (in USD)',
        default=lambda self: self.get_default_credit_limit(),
        currency_field='currency_usd_id',
        help='Total amount this customer is allowed to purchase on credit.')
    currency_usd_id = fields.Many2one(
        'res.currency', 'USD Currency', compute='_compute_currency_usd_id')

    # Never store this field as the value depends on the current company
    display_credit_limit = fields.Monetary(
        'Credit Limit', currency_field='credit_limit_currency_id',
        compute='_compute_display_credit_limit',
        inverse='_inverse_display_credit_limit')

    credit_limit_currency_id = fields.Many2one(
        'res.currency', 'Credit Limit Currency',
        compute='_compute_credit_limit_currency_id')

    @api.multi
    def _compute_display_credit_limit(self):
        usd = self.env.ref('base.USD')
        for partner in self:
            partner.display_credit_limit = usd.compute(
                partner.credit_limit, partner.credit_limit_currency_id)

    @api.multi
    def _inverse_display_credit_limit(self):
        usd = self.env.ref('base.USD')
        for partner in self:
            partner.credit_limit = partner.credit_limit_currency_id.compute(
                partner.display_credit_limit, usd)

    @api.multi
    def get_default_credit_limit(self):
        default_val = self.env.user.company_id.default_credit_limit
        return self.env.user.company_id.currency_id.compute(
            default_val, self.env.ref('base.USD'))

    @api.multi
    def _compute_currency_usd_id(self):
        usd = self.env.ref('base.USD')
        for partner in self:
            partner.currency_usd_id = usd

    @api.multi
    @api.constrains('credit_limit')
    @api.onchange('credit_limit')
    def check_amount(self):
        for customer in self:
            if customer.credit_limit < 0:
                raise exceptions.Warning(
                    'Credit Limit cannot be a negative number')

    @api.multi
    def _compute_credit_limit_currency_id(self):
        for partner in self:
            partner.credit_limit_currency_id = \
                partner.property_product_pricelist.currency_id
