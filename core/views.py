from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Category, Brand, Product, Customer, Order, OrderItem, Wishlist
from django.http import HttpResponseRedirect
from django.contrib import messages
import stripe
from django.conf import settings
from django.contrib.auth.views import LoginView
# from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

stripe.api_key = settings.STRIPE_SECRET_KEY


class CustomLoginView(LoginView):
    template_name = 'auth.html'
    redirect_authenticated_user = True

    def get_credentials(self):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        user = User.objects.filter(email__iexact=username).first()
        return {'username': user.username if user else username, 'password': password}

    def form_valid(self, form):
        credentials = self.get_credentials()
        user = authenticate(**credentials)
        if user:
            form.cleaned_data['username'] = credentials['username']
            return super().form_valid(form)
        form.add_error(None, "Invalid email or password.")
        return self.form_invalid(form)

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth.html', {'signup_active': True})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'auth.html', {'signup_active': True})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'auth.html', {'signup_active': True})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        Customer.objects.create(
            user=user,
            phone='',
            address=''
        )
        messages.success(request, "Account created successfully! Please sign in.")
        return render(request, 'auth.html', {'signup_active': False})
    return render(request, 'auth.html', {'signup_active': True})


def home(request):
    categories = Category.objects.filter(name__in=['Women', 'Men', 'Kids'])
    all_categories = Category.objects.all()
    context = {
        'main_categories': categories,
        'categories': all_categories,
    }
    return render(request, 'index.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(categories=category)
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'product_list.html', context)


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    products = Product.objects.filter(brand=brand)
    context = {
        'brand': brand,
        'products': products,
    }
    return render(request, 'product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {
        'product': product,
    }
    return render(request, 'product_detail.html', context)


@login_required
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not product.in_stock:
        messages.error(request, "This product is out of stock.")
        return redirect('product_detail', slug=slug)

    customer, created = Customer.objects.get_or_create(user=request.user)
    order, created = Order.objects.get_or_create(
        customer=customer, complete=False)

    order_item, created = OrderItem.objects.get_or_create(
        order=order, product=product)
    if not created:
        order_item.quantity += int(request.POST.get('quantity', 1))
    else:
        order_item.quantity = int(request.POST.get('quantity', 1))
    order_item.save()

    order.calculate_total()
    messages.success(request, f"{product.title} added to your cart!")
    return redirect('cart')


@login_required
def cart(request):
    customer = get_object_or_404(Customer, user=request.user)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    order.calculate_total()
    context = {
        'order': order,
        'order_total': order.total_price,
    }
    return render(request, 'cart.html', context)


@login_required
def remove_from_cart(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    if order_item.order.customer.user == request.user:
        order_item.delete()
        order_item.order.calculate_total()
        messages.success(request, "Item removed from your cart.")
    return redirect('cart')


@login_required
def checkout(request):
    customer = get_object_or_404(Customer, user=request.user)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        order.payment_method = payment_method

        # Update customer info
        customer.phone = request.POST['phone']
        customer.address = request.POST['address']
        customer.save()

        # Mock distance for COD (replace with Google Maps API later if needed)
        order.distance_km = float(request.POST.get('distance', 10))  # Default 10 km

        # Calculate totals
        order.calculate_total()

        if payment_method == 'cod':
            order.complete = True
            order.status = 'processing'
            # COD payment verified on delivery
            order.payment_status = 'pending'
            order.save()
            messages.success(
                request, "Order placed successfully with Cash on Delivery!")
            return redirect('profile')

        elif payment_method == 'online':
            payment_option = request.POST.get('payment_option')

            if payment_option == 'stripe':
                try:
                    session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price_data': {
                                 # Change to 'pkr' for Pakistan if needed
                                'currency': 'usd', 
                                'product_data': {'name': f'Order {order.id}'},
                                'unit_amount': int(order.total_price * 100),                            },
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url=request.build_absolute_uri(
                            '/payment-success/') + '?order_id=' + str(
                                order.id),
                        cancel_url=request.build_absolute_uri('/checkout/'),
                    )
                    return redirect(session.url)
                except stripe.error.StripeError as e:
                    messages.error(request, f"Payment error: {str(e)}")
                    return redirect('checkout')
            
            elif payment_option == 'bank':
                order.complete = True
                order.status = 'pending_payment'
                order.payment_status = 'pending'
                order.save()
                messages.info(
                    request, f"Please transfer ${order.total_price} to: Bank Name: HBL, Account: 1234567890123, IBAN: PK12HBLX0000001123456702. Use order ID {order.id} as reference. Email receipt to payments@yourfarfetch.com.")
                return redirect('profile')
    
    order.calculate_total()
    context = {
        'customer': customer,
        'order': order,
        'order_total': order.total_price,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'checkout.html', context)


def payment_success(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, complete=False)
    order.complete = True
    order.status = 'processing'
    order.payment_status = 'completed'
    order.save()
    messages.success(request, "Payment successful! Order placed.")
    return redirect('profile')


def payment_callback(request):
    # Placeholder for future gateways; redirect to checkout for now
    messages.info(request, "No payment processed.")
    return redirect('checkout')


@login_required
def profile(request):
    customer = get_object_or_404(Customer, user=request.user)
    context = {
        'customer': customer,
    }
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    customer = get_object_or_404(Customer, user=request.user)
    if request.method == 'POST':
        customer.phone = request.POST['phone']
        customer.address = request.POST['address']
        customer.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    context = {
        'customer': customer,
    }
    return render(request, 'edit_profile.html', context)


def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query) | Q(
            brand__name__icontains=query)
    )
    context = {
        'products': products,
        'title': f'Search Results for "{query}"',
    }
    return render(request, 'product_list.html', context)


def sale(request):
    products = Product.objects.filter(discount_price__isnull=False)
    context = {
        'products': products,
        'title': 'Sale',
    }
    return render(request, 'product_list.html', context)


def new_in(request):
    products = Product.objects.order_by('-id')[:20]
    context = {
        'products': products,
        'title': 'New In',
    }
    return render(request, 'product_list.html', context)


def brands(request):
    brands = Brand.objects.all()
    context = {
        'brands': brands,
    }
    return render(request, 'brands.html', context)


@login_required
def wishlist(request):
    customer = get_object_or_404(Customer, user=request.user)
    wishlist_items = Wishlist.objects.filter(customer=customer)
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)


@login_required
def add_to_wishlist(request, slug):
    product = get_object_or_404(Product, slug=slug)
    customer = get_object_or_404(Customer, user=request.user)
    wishlist_item, created = Wishlist.objects.get_or_create(
        customer=customer, product=product)
    if created:
        messages.success(request, f"{product.title} added to your wishlist!")
    else:
        messages.info(request, f"{product.title} is already in your wishlist.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))