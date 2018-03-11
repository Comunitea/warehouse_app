# -*- coding: utf-8 -*-
# Copyright 2017 Comunitea - <comunitea@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields

from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

class StockMove(models.Model):
    _inherit = "stock.move"

    restrict_package_id = fields.Many2one('stock.quant.package', string="From package")
    result_package_id = fields.Many2one('stock.quant.package', string="To package")
    package_qty = fields.Boolean('Package qty')

    @api.multi
    @api.onchange('result_package_id')
    def onchange_result_package_id(self):
        for move in self:
            if move.result_package_id:
                move.location_dest_id = move.result_package_id and move.result_package_id.location_id

    @api.multi
    @api.onchange('package_qty')
    def onchange_package_qty(self):
        for move in self:
            move.product_uom_qty = move.restrict_package_id and move.restrict_package_id.package_qty or 1

    @api.multi
    @api.onchange('restrict_package_id')
    def onchange_restrict_package_id(self, restrict_package_id=False, location_dest_id=False, partner_id=False):

        context = self._context.copy()
        context.update(cancel_event=True)

        for move in self:
            if move.restrict_package_id.multi:
                raise ValidationError("No puedes seleccionar un paquete multi")


            move.product_id = move.restrict_package_id and move.restrict_package_id.product_id or False
            move.onchange_product_id()
            move.product_uom_qty = move.restrict_package_id and move.restrict_package_id.package_qty or 0.00
            move.onchange_quantity()
            move.restrict_lot_id = move.restrict_package_id and move.restrict_package_id.lot_id or False
            move.result_package_id = move.restrict_package_id or False
            move.package_qty = True if move.restrict_package_id else False
            move.location_id = move.restrict_package_id and move.restrict_package_id.location_id or False



    @api.model
    def move_prepare_partial(self):
        forced_qties = {}
        if self.state not in ('assigned', 'confirmed', 'waiting'):
            return
        quants = self.reserved_quant_ids

        forced_qty = (self.state == 'assigned') and self.product_qty - sum([x.qty for x in quants]) or 0
        # if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
        if float_compare(forced_qty, 0, precision_rounding=self.product_id.uom_id.rounding) > 0:
            if forced_qties.get(self.product_id):
                forced_qties[self.product_id] += forced_qty
            else:
                forced_qties[self.product_id] = forced_qty
        for vals in self.picking_id._prepare_pack_ops(self.picking_id, quants, forced_qties):
            new_op = self.env['stock.pack.operation'].create(vals)

        self.picking_id.do_recompute_remaining_quantities()
        self.picking_id.write({'recompute_pack_op': False})
        return new_op and new_op.id or False

    @api.multi
    def action_done(self):
        ctx = self._context.copy()
        for move in self:
            if move.restrict_package_id:
                move.restrict_lot_id = move.restrict_package_id.lot_id
                ctx.update({'new_package_id': move.restrict_package_id.id})
            if move.result_package_id:
                ctx.update({'result_package_id': move.result_package_id.id})
        return super(StockMove, self.with_context(ctx)).action_done()

    @api.model
    def pda_move(self, vals):
        import ipdb; ipdb.set_trace()
        restrict_package_id = vals.get('restrict_package_id', False) or False
        location_dest_id = vals.get('location_dest_id', False)
        result_package_id = vals.get('result_package_id', 0)
        create_new_result = False
        package_qty = vals.get('package_qty', False)
        product_uom_qty = vals.get('product_uom_qty', 0.00)
        message = ''
        if restrict_package_id and restrict_package_id == result_package_id and package_qty != product_uom_qty:
            return {'message': 'No puedes mover un paquete si no es completo', 'id': 0}
        if product_uom_qty <=0:
            return {'message': 'No puedes una cantidad menor o igual a 0', 'id': 0}


        if result_package_id == 0:
            result_package_id = False
        elif result_package_id > 0 and result_package_id != restrict_package_id:
            result_package_id = self.env['stock.quant.package'].browse(result_package_id)
            if result_package_id.location_id and result_package_id.location_id.id != location_dest_id:
                return {'message': 'No puedes mover a un paquete que no está en la ubicación de destino', 'id': 0}
            result_package_id = result_package_id.id
        elif result_package_id < 0:
            create_new_result = True

        if not result_package_id:
            loc_dest = self.env['stock.location'].search_read([('id', '=', location_dest_id)], 'in_pack', limit=1)
            if loc_dest:
                need_check = loc_dest['in_pack']
                if need_check:
                    create_new_result = True

        if restrict_package_id:
            ##Paquete de origen
            restrict_package_id = self.env['stock.quant.package'].browse(restrict_package_id)
            restrict_lot_id = restrict_package_id.lot_id.id
            product_id = restrict_package_id.product_id
            if package_qty:
                product_uom_qty = restrict_package_id.package_qty
            location_id = restrict_package_id.location_id.id
            if not result_package_id and not create_new_result and package_qty:
                result_package_id = restrict_package_id.id

        else:
            ##Sin paquete de origen
            restrict_lot_id = vals.get('restrict_lot_id', False)
            product_id = self.env['product.product'].browse(vals.get('product_id', False))
            location_id = vals.get('location_id', False)


        if create_new_result:
            result_package_id = self.env['stock.quant.package'].create({}).id
            message = "Se ha creado un nuevo paquete %s"%result_package_id.name

        vals = {
            'origin': 'PDA done: [%s]'%self.env.user.name,
            'restrict_package_id': restrict_package_id and restrict_package_id.id,
            'restrict_lot_id': restrict_lot_id,
            'product_id': product_id.id,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty': product_uom_qty,
            'name': product_id.display_name,
            'location_id': location_id,
            'result_package_id': result_package_id,
            'location_dest_id': location_dest_id
        }
        print vals

        new_move = self.env['stock.move'].create(vals)
        if new_move:
            new_move.action_done()
            message = '%s Se ha creado: %s'%(message, new_move.display_name)
            return {'message': message, 'id': new_move.id}
        else:
            return {'message': 'Error al crear el movimeinto', 'id': 0}
