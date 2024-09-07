{
    "name": "OWL Services",
    "author": "IdeaCode Academy",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/odoo_services.xml",
        "views/barcode_model_views.xml",
    ],
    'controllers': [
        'controllers/main.py',
    ],
    "assets": {
        "web.assets_backend": [
            "owl_services/static/src/**/*"
        ]
    },
    "license": "LGPL-3"
}
