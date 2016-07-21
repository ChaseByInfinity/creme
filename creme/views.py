from creme import * 
# coding: utf-8


# index 
@app.route('/')
def index():
    try: 
        # get lcoation information for auto-locate and place in search bar on front page
        location = json.load(urlopen('http://ipinfo.io/json'))
        city = location['city']
        region = location['region']
        brands = []
        for brand in db.session.query(Shop.brand).distinct():
            brands.append(brand.brand)
        return render_template('index.html', city=city, region=region, brands=brands)
    
    except Exception as e:
        return str(e)


# User functions
#signup, not using wtforms because it's a bit static and hard to customize. some inconsistencies and the overall code of the signup is ugly, will be changed in the future
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    # remove try and except post-production
    try:
        if request.method == "POST":
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm = request.form['confirm']
            profile_picture = 'default.jpg'
            # validations, horrible semantics -- needs to be reformed
            if len(username) >= 4 and len(username) <= 20:
                x = User.query.filter(User.username == username).first()
                if not x:
                    if len(email) >= 4 and len(email) <= 60:
                        if password == confirm and len(password) > 4 and len(password) < 20:
                            hashedpw = sha256_crypt.encrypt(password)
                            newUser = User(username, email, hashedpw, profile_picture, datetime.now(), False)
                            db.session.add(newUser)
                            db.session.flush()
                            db.session.commit()

                            flash('Welcome to Creme')
                            session['logged_in'] = True
                            session['username'] = username

                            
                            return redirect(url_for('dashboard'))
                        else:
                            flash('Passwords do not match')
                            return render_template('index.html', signupmodal_active=True)
                    else:
                        flash('Your email is invalid')
                        return render_template('index.html', signupmodal_active=True)
                else:
                    flash('That username has already been taken')
                    return render_template('index.html', signupmodal_active=True)
            else:
                flash('Username must be between 4 and 20 characters')
                return render_template('index.html', signupmodal_active=True)
        return render_template('index.html')
                        
                        
            
            
            
        
    except Exception as e:
        return str(e)

#login function, straightforward, no changes needed in the future more than likely
@app.route('/login/', methods=['GET', 'POST'])
def login():
    try:
        
        if request.method == "POST":
            username = request.form['username']
            password = request.form['password']
            
            theUser = User.query.filter(User.username == username).first()
            
            if theUser:
                if sha256_crypt.verify(password, theUser.password):
                    session['logged_in'] = True
                    session['username'] = username
                    
                    flash('Welcome back!')
                    return redirect(url_for('dashboard'))
                    
                else:
                    flash('Password is incorrect')
                    return render_template('index.html', loginmodal_active = True)
            else:
                flash('Oops! We couldn\'t find that user')
                return render_template('index.html', loginmodal_active = True)
            
        return render_template('index.html')
            
            
        
    except Exception as e:
        return str(e)
#dashboard function, not sure what I want here yet
@app.route('/dashboard/')
@app.route('/dashboard/<int:page>', methods=['GET', 'POST'])
@login_required
def dashboard(page=1):
    # get username from session then return user data thru db query with username
    username = session['username']
    currUser = User.query.filter(User.username == username).first()
    id = currUser.id
    # get user checkins at coffee venues
    
    checkins = CheckIn.query.filter(CheckIn.by_user == id).order_by("date_checked desc").paginate(page, 7, False)
    
    # if user is an owner of any shops make a query so in the dashboard template we'll give them access to their shops
    
    shopsOwned = Shop.query.filter(Shop.owner == id).all()
    
    return render_template('dashboard.html', currUser = currUser, checkins=checkins, shopsOwned=shopsOwned)

#logout, straightforward
@app.route('/logout/')
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))


# account settings
@app.route('/settings/', methods=['GET', 'POST'])
@login_required
def edit_user():
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        
        
        if request.method == "POST":
            username = request.form['username']
            email = request.form['email']
            oldpassword = request.form['oldpassword']
            newpassword = request.form['newpassword']
            
            
          
            user.username = username
            user.email = email
      
            
            
            
            db.session.commit()
            session['username'] = username
            
            flash('Your settings have been updated')
            return redirect(url_for('edit_user'))
            
            
        return render_template('settings.html', user=user)
        
    except Exception as e:
        return str(e)
    

# below is the process that is carried out when a user wishes to designated that they own a coffee shop. there is no way to vet this process however we can add verification down the road that'll allow us to vet whether or not a venue is someone's and if it's legit
@app.route('/make/owner/')
@login_required
def make_owner():
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        
        if user.biz_owner == True:
            flash('You\'ve already designated yourself as a coffee shop owner')
            return redirect(url_for('dashboard'))
        
        else:
        
            user.biz_owner = True
            db.session.commit()
            db.session.flush()

            flash('You\'ve successfully designated your status as a coffee shop owner. You can now add your venue')
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        return str(e)
    
@app.route('/profile/change/', methods=['GET', 'POST'])
@login_required
def change_dp():
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        if request.method == 'POST':
        # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                user.profile_picture = str(file.filename)
                db.session.commit()
                db.session.flush()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash('Profile picture updated!')
                return redirect(request.url)
        
        return render_template('dp_update.html', user=user)
    except Exception as e:
        return str(e)
    
#conversely, just in case a user accidentally makes themselves an owner, lets give them the option to rectify that
@app.route('/remove/owner/')
@login_required
def remove_owner():
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        
        user.biz_owner = False
        db.session.commit()
        db.session.flush()
        
        flash('You no longer hold owner status')
        return redirect(url_for('dashboard'))
        
        
    except Exception as e:
        return str(e)

# manage shops owned by user
@app.route('/manage/mine/')
@login_required
def manage_mine():
    try:
        # verify current user is biz owner
        
        username = session['username']
        currentUser = User.query.filter(User.username == username).first()
        
        if currentUser.biz_owner == False:
            flash('You aren\'t a designated coffee shop owner')
            return redirect(url_for('dashboard'))
            
        else:
            shopsOwned = Shop.query.filter(Shop.owner == currentUser.id).all()
            
        
        return render_template('manage_mine.html', shopsOwned=shopsOwned)
    except Exception as e:
        return str(e)

    
# edit shop owned by user
@app.route('/shop/edit/<shop_id>', methods=['GET', 'POST'])
@login_required
def shop_edit(shop_id):
    try:
        
        username = session['username']
        user = User.query.filter(User.username == username).first()
        
        currentShop = Shop.query.get(shop_id)
        
        if not currentShop:
            flash('Shop doesn\'t exist')
            return redirect(url_for('dashboard'))
        
        if not currentShop.owner == user.id:
            flash('You\'re not the owner of this shop')
            return redirect(url_for('dashboard'))
        
        
        
        if request.method == 'POST':
            brand = request.form['brand']
            address = request.form['address']
            city = request.form['city']
            state = request.form['state']
            postal = request.form['postal']
            country = request.form.get('country')
            
            
            currentShop.brand = brand
            currentShop.address = address
            currentShop.city = city
            currentShop.state = state
            currentShop.postal = postal
            currentShop.country = country
            
            address = str(address) + ', ' + str(city)
            api_key = 'AIzaSyC6Kyo138gBcEUAS2YJUWaSgBrJrpeLDoA'
            api_response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(address, api_key))
            api_response_dict = api_response.json()
                # if api response is good, it'll assign lat and lng for db entry
            if api_response_dict['status'] == 'OK':
                latitude = api_response_dict['results'][0]['geometry']['location']['lat']
                longitude = api_response_dict['results'][0]['geometry']['location']['lng']

            currentShop.lat = latitude
            currentShop.lon = longitude
            db.session.commit()
            db.session.flush()
            
            flash('Changes saved!')
            return redirect(url_for('manage_mine'))
        
        
        return render_template('edit_shop.html', currentShop=currentShop)
    
    except Exception as e:
        return str(e)

# delete shop owned by user
@app.route('/shop/delete/<shop_id>')
@login_required
def delete_shop(shop_id):
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        
        currentShop = Shop.query.get(shop_id)
        
        if not currentShop.owner == user.id:
            flash('You\'re not the owner of this shop')
            return redirect(url_for('dashboard'))
        
        if not currentShop:
            flash('Shop doesn\'t exist')
            return redirect(url_for('dashboard'))
        
        
        
        db.session.delete(currentShop)
        db.session.commit()
        db.session.flush()
        
        flash('Shop deleted :(')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        return str(e)

# Search and coffee
#the search method,  uses vincenty to append each to a list within a certain radius then querys that list and returns data to results page
@app.route('/search/', methods=['GET', 'POST'])
@app.route('/search/<int:page>', methods=['GET', 'POST'])
def search(page=1):
    try:
        # submit index form 
        if request.method == 'POST':
            # get user location, value is automatically generated using freeip json output
            userLoc = request.form['location']
            brand = request.form.get('brand')
            # instantiate the geolocator to convert the users location to a pair of lat and long
            geolocator = Nominatim()
            location = geolocator.geocode(userLoc)
            # round both to two decimals to get shops within a larger radius, more accuracy
            latitude = location.latitude
            longitude = location.longitude
            
            brand = request.form.get('brand')
           
            results = Shop.query.all()
            list = []
            
            for result in results:
                if vincenty((result.lat, result.lon), (latitude, longitude)).miles < 25:
                    list.append(result.address)
                    
            if brand:       
                shops = Shop.query.filter(Shop.address.in_(list), Shop.brand == brand ).all()
            else:
                shops = Shop.query.filter(Shop.address.in_(list)).all()
            
            
            
            
            
            
        return render_template('results.html', list=list, shops=shops)
        
        
    except Exception as e:
        return str(e)
    
#shop display with menu information and such
    
@app.route('/shop/<shop_id>', methods=['GET', 'POST'])
def view_shop(shop_id):
    try:
        
        shop = Shop.query.get(shop_id)
        
        if not shop:
            error = 'Shop not found'
            return render_template('no_shop.html', error=error)
        
        
        items = []
        for coffee in db.session.query(Item.name).filter(Item.from_shop == shop.brand).distinct():
            items.append(coffee.name)
            
        sizes = []
        
        for size in db.session.query(Item.size).filter(Item.from_shop == shop.brand).distinct():
            sizes.append(size.size)
        
        ourItem = None
        if request.method == 'POST':
            item = request.form.get('type')
            size = request.form.get('size')
            
            
            ourItem = Item.query.filter(Item.name == item, Item.size == size).first()
        
        
        return render_template('shop.html', shop=shop, items=items, sizes=sizes, ourItem=ourItem)
        
    except Exception as e:
        return str(e)
    
    
#checkin to coffee shop

@app.route('/checkin/<shop_id>')
@login_required
def check_in(shop_id):
    try:
        username = session['username']
        activeUser = User.query.filter(User.username == username).first()
        
        shop = Shop.query.get(shop_id)
        
        newCheckIn = CheckIn(shop.brand, shop.address, activeUser.id, datetime.now())
        db.session.add(newCheckIn)
        db.session.flush()
        db.session.commit()
        
        flash('Checked in to ' + str(shop.brand) + ' on ' + str(shop.address))
        return redirect(url_for('dashboard'))
        
        
    except Exception as e:
        return str(e)
    
    
    
# Here we begin the new venue option. This will allow user-contributed content. No way to vet it currently. Maybe a Google Maps query to make sure it exists?
@app.route('/shop/new/', methods=['GET', 'POST'])
@login_required
def new_shop():
    try:
        # get user information for input into owner column
        username = session['username']
        currentUser = User.query.filter(User.username == username).first()
        id = currentUser.id
        
        #if form sent
        if request.method == 'POST':
        
            # check to see if all form variables were entered, not using WTForms maybe will because this is waaaaay too dirty (avoid 400 error)
            if request.form['brand'] and request.form['address'] and request.form['city'] and request.form['state'] and request.form['postal'] and request.form.get('country'):
                brand = request.form['brand']
                address = request.form['address']
                city = request.form['city']
                state = request.form['state']
                postal = request.form['postal']
                country = request.form.get('country')
                
                # parse address and city to string which will be plugged into address variable that'll be passed to the google maps api for lat lng
                address = str(address) + ', ' + str(city)
                api_key = 'AIzaSyC6Kyo138gBcEUAS2YJUWaSgBrJrpeLDoA'
                api_response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(address, api_key))
                api_response_dict = api_response.json()
                # if api response is good, it'll assign lat and lng for db entry
                if api_response_dict['status'] == 'OK':
                    latitude = api_response_dict['results'][0]['geometry']['location']['lat']
                    longitude = api_response_dict['results'][0]['geometry']['location']['lng']

                # db entry and success
                newShop = Shop(brand, address, city, state, postal, country, latitude, longitude, id)
                db.session.add(newShop)
                db.session.flush()
                db.session.commit()

                flash('Your shop has been added and is now searchable!')
                return redirect(url_for('dashboard'))
            #error
            else:
                flash('You must fill out all fields')
                return redirect(url_for('new_shop'))
        
        return render_template('new_shop.html')
    except Exception as e:
        return str(e)
    
    
#add shop item
@app.route('/shop/additem/<shop_id>', methods=['GET', 'POST'])
@login_required
def add_item(shop_id):
    try:
        shop = Shop.query.get(shop_id)
        username = session['username']
        user = User.query.filter(User.username == username).first()
        if not shop.owner == user.id:
            flash('You are not the owner of this shop')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
             if request.form['name'] and request.form['size'] and request.form['calories'] and request.form['protein'] and request.form['fat']:
                    name = request.form['name']
                    size = request.form['size']
                    calories = request.form['calories']
                    protein = request.form['protein']
                    fat = request.form['fat']
                    from_shop = shop.brand
                    
                    newItem = Item(name, size, from_shop, calories, protein, fat)
                    db.session.add(newItem)
                    db.session.flush()
                    db.session.commit()
                    flash('Item added')
                    return redirect(url_for('manage_mine'))
                    
                    
             else:
                    flash('Please enter all fields')
                    return redirect(request.url)
                    
                    
        
        return render_template('add_item.html', shop=shop)
        
    except Exception as e:
        return str(e)
    
#items from shop
@app.route('/shop/items/<shop_id>')
@login_required
def view_items(shop_id):
    try:
        
        shop = Shop.query.get(shop_id)
        from_shop = shop.brand
        
        items = Item.query.filter(Item.from_shop == from_shop).all()
        
        return render_template('view_items.html', items=items)
    except Exception as e:
        return str(e)
    
#edit item
@app.route('/item/edit/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        id = user.id
        item = Item.query.get(item_id)
        brand = item.from_shop
        shop = Shop.query.filter(Shop.brand == brand).first()
        
        if not shop.owner == id:
            flash('You do not own the shop where this item is located')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            name = request.form['name']
            size = request.form['size']
            calories = request.form['calories']
            protein = request.form['protein']
            fat = request.form['fat']
            
            item.name = name
            item.size = size
            item.calories = calories
            item.protein = protein
            item.fat = fat
            
            db.session.commit()
            db.session.flush()

            flash('Item updated')
            return redirect(request.url)
        
        return render_template('edit_item.html', item=item)
        
    except Exception as e:
        return str(e)

#delete item
@app.route('/item/delete/<item_id>')
@login_required
def delete_item(item_id):
    try:
        username = session['username']
        user = User.query.filter(User.username == username).first()
        id = user.id
        item = Item.query.get(item_id)
        brand = item.from_shop
        shop = Shop.query.filter(Shop.brand == brand).first()
        
        if not shop.owner == id:
            flash('You do not own the shop where this item is located')
            return redirect(url_for('dashboard'))
        
        db.session.delete(item)
        db.session.commit()
        db.session.flush()
        
        flash('Item removed')
        
        return redirect(url_for('manage_mine'))
        
        
    except Exception as e:
        return str(e)
    
    
    
# custom error pages
@app.errorhandler(404)
def page_404(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_500(e):
    return render_template('500.html'), 500
        
