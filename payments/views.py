# payments/views.py

# from django.views.generic.base import TemplateView

# class HomePageView(TemplateView):
#     template_name = 'home.html'



# payments/views.py
from django.conf import settings # new
from django.http.response import JsonResponse # new
from django.views.decorators.csrf import csrf_exempt # new
from django.views.generic.base import TemplateView

import stripe

from django.http.response import JsonResponse, HttpResponse


class HomePageView(TemplateView):
    template_name = 'home.html'

# 1. Get Publishable Key
# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

# 2. Create Checkout Session
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                # new
                client_reference_id=request.user.id if request.user.is_authenticated else None,

                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                # line_items=[
                #     {
                #         'name': 'T-shirt',
                #         'quantity': 1,
                #         'currency': 'usd',
                #         'amount': '2000',
                #     }
                # ]

                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'T-shirt',
                            },
                            'unit_amount': 2000,  # in cents
                        },
                        'quantity': 1,
                    }
                ]

                # Latest Dynamic
                # line_items=[
                #     {
                #         "price": "prod_THU46JtpGjDzqB", "quantity": 1
                #     }
                # ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

# 3. Redirect the User Appropriately
class SuccessView(TemplateView):
    template_name = 'success.html'

class CancelledView(TemplateView):
    template_name = 'cancelled.html'


# 4. Confirm Payment with Stripe Webhooks
@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    # https://docs.stripe.com/api/events/types
    if event['type'] == 'checkout.session.completed': # events which are called whenever a checkout is successful
        print("Payment was successful.")
        # TODO: run some custom code here

    return HttpResponse(status=200)
