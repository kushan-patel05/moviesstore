from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item, CheckoutFeedback
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def index(request):
    cart_total = 0
    movies_in_cart = []
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())
    if (movie_ids != []):
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(cart, movies_in_cart)

    template_data = {}
    template_data['title'] = 'Cart'
    template_data['movies_in_cart'] = movies_in_cart
    template_data['cart_total'] = cart_total
    return render(request, 'cart/index.html', {'template_data': template_data})

def add(request, id):
    get_object_or_404(Movie, id=id)
    cart = request.session.get('cart', {})
    cart[id] = request.POST['quantity']
    request.session['cart'] = cart
    return redirect('cart.index')

def clear(request):
    request.session['cart'] = {}
    return redirect('cart.index')

@login_required
def purchase(request):
    cart = request.session.get('cart', {})
    movie_ids = list(cart.keys())

    if (movie_ids == []):
        return redirect('cart.index')
    
    movies_in_cart = Movie.objects.filter(id__in=movie_ids)
    cart_total = calculate_cart_total(cart, movies_in_cart)

    order = Order()
    order.user = request.user
    order.total = cart_total
    order.save()

    for movie in movies_in_cart:
        item = Item()
        item.movie = movie
        item.price = movie.price
        item.order = order
        item.quantity = cart[str(movie.id)]
        item.save()

    request.session['cart'] = {}
    template_data = {}
    template_data['title'] = 'Purchase confirmation'
    template_data['order_id'] = order.id
    return render(request, 'cart/purchase.html', {'template_data': template_data})

@require_POST
@login_required
def submit_feedback(request):
    order_id = request.POST.get('order_id')
    name = request.POST.get('name', '')
    statement = request.POST.get('statement', '')
    if not statement or not order_id:
        return JsonResponse({ 'ok': False, 'error': 'Missing fields' }, status=400)
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({ 'ok': False, 'error': 'Order not found' }, status=404)
    CheckoutFeedback.objects.create(order=order, name=name, statement=statement)
    return JsonResponse({ 'ok': True })

def feedback_list(request):
    entries = CheckoutFeedback.objects.order_by('-created_at')
    template_data = { 'title': 'Checkout Feedback', 'entries': entries }
    return render(request, 'cart/feedback_list.html', { 'template_data': template_data })