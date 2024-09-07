# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################

{
    "name": "Riocabo reports",
    "version": '17.0.1.0.0',
    "category": "Sales",
    "author": "Serincloud",
    "maintainer": "Serincloud",
    "website": "www.ingenieriacloud.com",
    "license": "AGPL-3",
    "depends": [
        "sale_management",
        "account",
    ],
    "data": [
        "views/report_invoice_document.xml",
        "views/report_saleorder_document.xml",
    ],
    "installable": True,
}
