# -*- coding: utf-8 -*-
# Copyright 2017 Comunitea - <comunitea@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Warehouse App",
    "summary": "Warehouse app",
    "version": "10.0.1.0.0",
    "category": "Inventory, Logistic, Storage",
    "website": "https://www.comunitea.com",
    "author": "Kiko Sánchez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/stock_location.xml',
        'views/stock_quant_package.xml',
        'views/stock_location_rack.xml',
        'views/stock_move.xml'

    ],
}
