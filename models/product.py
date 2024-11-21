class Product:
    def __init__(self, name, description, price, stock, category_id, image_url=None):
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.category_id = category_id
        self.image_url = image_url