from app import app, db, Brand, Model

# Dictionary of brands and models
brands_and_models = {
    'Toyota': ['Corolla', 'Camry', 'RAV4', 'Highlander', 'Tacoma'],
    'Honda': ['Civic', 'Accord', 'CR-V', 'Pilot', 'Fit'],
    'Ford': ['F-150', 'Mustang', 'Explorer', 'Focus', 'Escape'],
    'Chevrolet': ['Silverado', 'Malibu', 'Equinox', 'Tahoe', 'Camaro'],
    'BMW': ['3 Series', '5 Series', 'X3', 'X5', 'M4'],
    'Nissan': ['Altima', 'Sentra', 'Rogue', 'Pathfinder', 'Frontier']
}

with app.app_context():
    for brand_name, model_list in brands_and_models.items():
        # Check if brand already exists
        brand = Brand.query.filter_by(brand_name=brand_name).first()
        if not brand:
            brand = Brand(brand_name=brand_name)
            db.session.add(brand)
            db.session.commit()

        for model_name in model_list:
            # Check if model already exists for this brand
            existing_model = Model.query.filter_by(model_name=model_name, brand_id=brand.brand_id).first()
            if not existing_model:
                model = Model(model_name=model_name, brand_id=brand.brand_id)
                db.session.add(model)

    db.session.commit()

    # Print out models to confirm
    models = Model.query.all()
    print("Models in DB:", [(m.model_id, m.model_name) for m in models])
