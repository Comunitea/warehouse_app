# -*- coding: utf-8 -*-
# Copyright 2017 Comunitea - <comunitea@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models, fields
import odoo.addons.decimal_precision as dp

from odoo.exceptions import ValidationError



SEARCH_OPTIONS = {'stock.quant.package': 'name',
                  'stock.production.lot': 'name',
                  'stock.location': 'barcode',
                  'product.product': 'barcode'}

FIELD_NAME = {'stock.quant.package': 'name',
              'stock.production.lot': 'name',
              'stock.location': 'barcode',
              'product.product': 'display_name'}

FIELDS = {'stock.quant.package': ['id', 'name', 'lot_id', 'lot_id_name', 'location_id', 'location_id_name', 'package_qty', 'multi', 'product_id', 'product_id_name', 'uom'],
          'stock.production.lot': ['id', 'name', 'product_id', 'product_id_name', 'use_date', 'life_date', 'location_id'],
          'stock.location': ['id', 'name', 'usage', 'barcode'],
          'product.product': ['id', 'name', 'barcode', 'default_code', 'default_stock_location_id', 'default_stock_location_id_name', 'tracking']}


INFO_FIELDS = {'stock.quant.package': ['id', 'name', 'lot_id', 'location_id','package_qty', 'multi', 'product_id', 'uom_id', 'quant_ids', 'children_ids'],
              'stock.production.lot': ['id', 'name', 'product_id', 'use_date', 'removal_date', 'qty_available', 'quant_ids', 'display_name', 'uom_id', 'location_id'],
              'stock.location': ['id', 'name', 'usage', 'barcode', 'need_check'],
              'product.product': ['id', 'display_name', 'name', 'barcode', 'default_code', 'default_stock_location_id', 'tracking', 'uom_id', 'qty_available'],
              'stock.picking': ['id', 'name', 'picking_type_id', 'user_id', 'min_date', 'state', 'location_id', 'location_dest_id', 'wave_id', 'priority', 'remaining_ops', 'pack_operation_count', 'pack_operation_ids'],
              'stock.pack.operation': ['id', 'display_name', 'package_id', 'product_id', 'pack_lot_ids', 'pda_product_id', 'pda_done', 'is_done' , 'product_qty', 'qty_done', 'ordered_qty'],
              'stock.pack.operation.lot': ['id', 'display_name', 'lot_id', 'qty', 'qty_todo']}

INFO_FIELDS_M2O = {'stock.quant.package': ['id', 'name', 'location_id', 'package_qty', 'multi', 'product_id', 'uom_id'],
                  'stock.production.lot': ['id', 'name', 'use_date', 'location_id', 'qty_available', 'display_name', 'uom_id', 'location_id'],
                  'stock.location': ['id', 'name', 'usage', 'barcode', 'need_check'],
                  'stock.quant':['id', 'display_name', 'lot_id', 'location_id', 'qty', 'reservation_id', 'in_date'],
                  'product.uom': ['id', 'name'],
                  'res.users':  ['id', 'name'],
                  'stock.pack.operation': ['id', 'display_name', 'package_id', 'product_id', 'pack_lot_ids', 'pda_product_id', 'pda_done', 'is_done', 'product_qty', 'qty_done', 'ordered_qty'],
                  'stock.pack.operation.lot': ['id', 'display_name', 'lot_id', 'qty', 'qty_todo'],
                  'stock.picking.type': ['id', 'name', 'show_in_pda', 'short_name', 'code', 'use_create_lots', 'use_existing_lots', 'show_entire_packs'],
                  'product.product': ['id', 'display_name', 'barcode', 'name', 'default_code', 'default_stock_location_id', 'tracking']}


class WarehouseApp (models.Model):

    _name = 'warehouse.app'

    @api.model
    def get_app_fields(self, id):

        object_id = self.browse(id)
        fields = {}
        if object_id:
            for field in fields:
                fields[field] = object_id[field]
        return fields

    @api.model
    def get_info_object(self, vals):
        model = vals.get('model', False)
        id = vals.get('id', False)
        object_id = self.env[model].browse(id)
        field_value = {}
        if not object_id:
            return False
        for field in INFO_FIELDS[model]:
            if object_id.fields_get(field)[field]['type'] == 'many2one':
                field_value[field] = self.get_m2o_vals(object_id, field)
            elif object_id.fields_get(field)[field]['type'] == 'one2many':

                field_value[field] = self.get_o2m_vals(object_id, field)
            else:
                field_value[field] = object_id[field]
            print "---------%s\n\n\n%s\n\n"%(field, field_value)

        res = {'model': model, 'id': id, 'values': field_value}
        return res


    def get_m2o_vals(self, object_id, field):
         print "-----------%s"%object_id
         #import ipdb; ipdb.set_trace()
         if object_id[field]:
             sub_values = {}
             submodel = object_id.fields_get(field)[field]['relation']
             print "-------------------%s"%field
             for sub_field in INFO_FIELDS_M2O[submodel]:
                 print "-------------------%s  >>>  %s" % (field, sub_field)
                 if object_id[field].fields_get(sub_field)[sub_field]['type'] == 'many2one':
                     sub_values[sub_field] = self.get_m2o_val(object_id[field][sub_field])
                 if object_id[field].fields_get(sub_field)[sub_field]['type'] == 'one2many':
                     sub_values[sub_field] = self.get_o2m_vals(object_id[field], sub_field)
                 else:
                     sub_values[sub_field] = object_id[field][sub_field]
         else:
             sub_values = False
         return sub_values

    def get_m2o_val(self, val):
        if len(val)>0:
            return {'id': val.id, 'name': val.name}
        else:
            return False

    def get_o2m_vals(self, object_id, field):

        submodel = object_id.fields_get(field)[field]['relation']  #if vals['product_id']:
        sub_model_id_values = []
        for sub_model_id in object_id[field]:
            sub_values = {}
            for sub_field in INFO_FIELDS_M2O[submodel]:
                if sub_model_id.fields_get(sub_field)[sub_field]['type'] == 'many2one':
                    sub_values[sub_field] = self.get_m2o_val(sub_model_id[sub_field])
                elif sub_model_id.fields_get(sub_field)[sub_field]['type'] == 'one2many':
                    print "Falla aqui"

                    sub_values[sub_field] = self.get_o2m_vals(sub_model_id, sub_field)
                    print "No Fallo"
                else:
                    sub_values[sub_field] = sub_model_id[sub_field]
            sub_model_id_values.append(sub_values)
        return sub_model_id_values


    @api.model
    def get_object_id(self, vals):

        print "Recibo %s" % vals
        model = vals.get('model', False)
        id = vals.get('id', False)
        if id and model:
            return self.get_info_object({'id': id, 'model': model})

        object_id = False
        res = {}
        return_object = vals.get('return_object', False)
        field_value = {}
        default_domain = vals.get('domain', False)
        search_str = vals.get('search_str')

        if search_str:
            search_options = list(set(SEARCH_OPTIONS.keys()) & set(model))
            for option in search_options:
                domain = [(SEARCH_OPTIONS[option], '=', search_str)]
                if default_domain:
                    domain += default_domain
                val_id = self.env[option].search_read(domain, ['id'], limit=1)
                if val_id:
                    id = val_id[0]['id']
                    break

        if id:
            res = self.get_info_object({'id': id, 'model': option})
        else:
            res = {'model': SEARCH_OPTIONS.keys(), 'id': 0,  'message': 'No se ha encontrado un objeto para %s'%search_str}

        print "Retorno %s"%res

        return res



    @api.model
    def get_object_id_V10(self, vals):

        print "Recibo %s"%vals
        res = {}
        model = vals.get('model', False)
        return_object = vals.get('return_object', False)
        field_value = {}

        if not model:
            search_options = SEARCH_OPTIONS.keys()
        elif model == ['stock.qty']:
            qty = vals.get('qty')
            try:
                qty = float(qty.replace(',','.')) or 0.00
            except:
                qty = 0.00
            res = {'model': 'stock.qty', 'id': 0, 'name': qty}
        else:
            search_options = list(set(SEARCH_OPTIONS.keys()) & set(model))
            search_str = vals.get('search_str')
            if search_str:
                search_options = list(set(SEARCH_OPTIONS.keys()) & set(model))
                for option in search_options:
                    model = option
                    domain = [(SEARCH_OPTIONS[option], '=', search_str)]
                    object_id = self.env[model].search(domain, limit=1)
                    if object_id:
                        break
            else:
                id = vals.get('id', False)
                if id:
                    object_id = self.env[model].browse(id)
                    print model, id, object_id
            if object_id:
                res = {'model': model, 'id': object_id.id, 'name': FIELD_NAME[model]}
                if return_object:
                    for field in FIELDS[model]:
                        type = object_id.fields_get(field)[field]['type']
                        if type == 'many2one':
                            field_value[field] = object_id[field]['id'], object_id[field]['name']
                        elif type in ('many2many', 'one2man'):
                            for depend_id in object_id.field:
                                field_value[field] += [depend_id.id, depend_id.name]
                        else:
                            field_value[field] = object_id[field]
                    res['fields'] = field_value
            else:
                res = {'model': model, 'id': 0, 'name': FIELD_NAME[model], 'message': 'No se ha encontrado un %s para %s'%(model, search_str)}

        print "Retorno %s"%res
        return res

