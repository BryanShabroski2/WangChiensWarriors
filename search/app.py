from flask import Flask, render_template, request, abort
import func

app = Flask(__name__)

@app.route("/", methods=["GET"])
def search():
    keywords  = request.args.get("keywords", "")
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")

    results = func.search_products(keywords, min_price, max_price)
    return render_template(
        "search.html",
        results=results,
        keywords=keywords,
        min_price=min_price,
        max_price=max_price
    )

@app.route("/product/<int:listing_id>")
def product_detail(listing_id):
    detail = func.get_product_detail(listing_id)
    if not detail:
        abort(404)
    return render_template("product.html", p=detail)

if __name__ == "__main__":
    app.run(debug=True)
