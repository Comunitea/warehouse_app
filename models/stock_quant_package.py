# -*- coding: utf-8 -*-
# Copyright 2017 Comunitea - <comunitea@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
import odoo.addons.decimal_precision as dp

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.multi
    def get_package_info(self):
        for package in self:
            if package.children_ids:
                package.multi = True
                package.product_id = False
                package.package_qty = 0.00
                package.lot_ids = package.children_ids.mapped('quant_ids').mapped('lot_id')
            else:
                package.multi = False
                package.package_qty = sum(quant.qty for quant in package.quant_ids)
                package.product_id = package.quant_ids and package.quant_ids[0].product_id or False
                package.lot_ids = package.quant_ids.mapped('lot_id')


            if len(package.lot_ids) == 1:
                package.lot_id = package.lot_ids[0]
            else:
                package.lot_id = False


    package_qty = fields.Float('Quantity',
                               digits_compute=dp.get_precision('Product Unit of Measure'),
                               compute=get_package_info, multi=True)
    product_id = fields.Many2one('product.product', 'Product', compute=get_package_info, multi=True)
    lot_ids = fields.One2many('stock.production.lot', string="Lot", compute=get_package_info, multi=True)
    lot_id = fields.Many2one('stock.production.lot', string="Lot", compute=get_package_info, multi=True)
    multi = fields.Boolean('Multi', compute=get_package_info, multi=True)
    uom_id = fields.Many2one(related='product_id.uom_id')
    tracking = fields.Selection(related='product_id.tracking', readonly=True)

    @api.model
    def check_inter(self, old, new):
        return (old.product_id == new.product_id) and new.package_qty > 0

    @api.model
    def name_to_id(self, name):
        package = self.search([('name', '=', name)], limit=1)
        return package or False

    @api.model
    def get_app_fields(self, id):

        object_id = self.browse(id)
        fields = {}
        if object_id:
            for field in fields:
                fields[field] = object_id[field]
        return fields


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    @api.multi
    def get_lot_info(self, location_id=False):
        for lot in self:

            if location_id:
                internal_quants = lot.quant_ids.\
                    filtered(lambda x: x.location_id.id == location_id and x.location_id.usage == 'internal')
            else:
                internal_quants = lot.quant_ids.\
                    filtered(lambda x: x.location_id.usage == 'internal')

            lot_qty = sum(internal_quants.mapped('qty'))
            lot.qty_available = lot_qty
            location_id = list(set(internal_quants.mapped('location_id').mapped('id')))
            if len(location_id) == 1:
                lot.location_id = location_id
            else:
                lot.location_id = False

    location_id = fields.Many2one('stock.location', compute="get_lot_info", multi=True)
    qty_available = fields.Float('Qty', compute="get_lot_info", multi=True)
    uom_id = fields.Many2one(related='product_id.uom_id')

    @api.onchange('product_id')
    def get_display_name(self):

        if self.product_id and False:
            self.display_name = self.name & "." & self.product_id.default_code
        else:
            self.display_name = self.name

    @api.multi
    def write(self, vals):
        return super(StockProductionLot, self).write(vals)
