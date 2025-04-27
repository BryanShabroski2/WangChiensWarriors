from flask import Flask, render_template, request, redirect, url_for, abort
import func

app = Flask(__name__)

@app.route('/')
def manage():
    listings = func.get_active_listings()
    return render_template('manage.html', listings=listings)

@app.route('/publish', methods=['GET','POST'])
def publish():
    if request.method == 'POST':
        func.publish_product(
            category     = request.form['category'],
            product_name = request.form['product_name'],
            title        = request.form['title'],
            desc         = request.form['desc'],
            qty          = int(request.form['qty']),
            price        = float(request.form['price'])
        )
        return redirect(url_for('manage'))
    categories = func.get_categories()
    return render_template('publish.html', categories=categories)

@app.route('/edit/<int:listing_id>', methods=['GET','POST'])
def edit(listing_id):
    if request.method == 'POST':
        func.edit_listing(
            listing_id,
            category     = request.form.get('category'),
            product_name = request.form.get('product_name'),
            title        = request.form.get('title'),
            desc         = request.form.get('desc'),
            qty          = int(request.form.get('qty',0)),
            price        = float(request.form.get('price',0.0))
        )
        return redirect(url_for('manage'))
    listing    = func.get_listing(listing_id)
    if not listing:
        abort(404)
    categories = func.get_categories()
    return render_template('edit.html', listing=listing, categories=categories)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    func.update_quantity(
        int(request.form['listing_id']),
        int(request.form['qty'])
    )
    return redirect(url_for('manage'))

@app.route('/toggle_status', methods=['POST'])
def toggle_status():
    func.toggle_status(int(request.form['listing_id']))
    return redirect(url_for('manage'))

@app.route('/delete', methods=['POST'])
def delete():
    func.delete_listing(int(request.form['listing_id']))
    return redirect(url_for('manage'))


@app.route('/request_category', methods=['POST'])
def request_category():
    # pull in the three modal fields
    new_cat   = request.form.get('requested_category')
    prod_name = request.form.get('requested_product_name')
    desc      = request.form.get('requested_description')

    print(f"[Category Request] category={new_cat!r}, product={prod_name!r}, desc={desc!r}")


    return redirect(url_for('publish'))

if __name__ == '__main__':
    app.run(debug=True)
