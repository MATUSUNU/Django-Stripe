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
        # You use safe=False when you're returning a list, string, or any non-dict JSON-serializable object.
        return JsonResponse(stripe_config, safe=False)

# 2. Create Checkout Session
@csrf_exempt # This Django decorator disables Cross-Site Request Forgery (CSRF) protection for this view.
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

                # line_items=[
                #     {
                #         'price_data': {
                #             'currency': 'usd',
                #             'product_data': {
                #                 'name': 'T-shirt',
                #             },
                #             'unit_amount': 2000,  # in cents
                #         },
                #         'quantity': 1,
                #     }
                # ]

                # Latest Dynamic
                line_items=[
                    {
                        "price": "price_1SKv6TBDCFiWwdWZIbcpo4QK",

                        "quantity": 1
                    }
                ]
            )
            # Not supported anymore
            # return JsonResponse({'sessionId': checkout_session['id']})

            return JsonResponse({'sessionUrl': checkout_session.url})
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
    # stripe.api_key = settings.STRIPE_SECRET_KEY

    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    event = None

    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, endpoint_secret
    #     )
    # except ValueError as e:
    #     # Invalid payload
    #     return HttpResponse(status=400)
    # except stripe.error.SignatureVerificationError as e:
    #     # Invalid signature
    #     return HttpResponse(status=400)

    if endpoint_secret:
        # Only verify the event if you've defined an endpoint secret
        # Otherwise, use the basic event deserialized with JSON
        # sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    # https://docs.stripe.com/api/events/types
    # if event['type'] == 'checkout.session.completed': # events which are called whenever a checkout is successful
    #     print("Payment was successful.")
    #     # TODO: run some custom code here

    # Handle the event [Your webhook gets called multiple times:]
    if event.type == 'checkout.session.completed':
        session = event.data.object

        # 1. Get order from database using session ID
        # 2. Update order status to "processing" or "pending_payment" (NOT "paid")
        # 3. Store Stripe payment intent ID for future reference
        # 4. DO NOT update inventory or send confirmation yet
        # 5. Optional: Send "payment processing" email to customer

        print(f"Checkout process completed, waiting for payment confirmation: {session.id}")

    elif event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object

        # 1. Find order using payment_intent.id (from checkout.session.completed)
        # 2. Update order status to "paid" or "completed"
        # 3. Update inventory/stock levels (reduce quantity)
        # 4. Send order confirmation email to customer
        # 5. Trigger internal notifications (Slack, etc.)
        # 6. Log successful payment for analytics

        print(f"Payment confirmed, fulfilling order for payment: {payment_intent.id}")

    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object

        # 1. Find order using payment_intent.id
        # 2. Update order status to "payment_failed"
        # 3. Send payment failure email to customer with retry instructions
        # 4. Alert customer support for follow-up
        # 5. DO NOT update inventory (stock remains unchanged)

        print(f"Payment failed, order not fulfilled: {payment_intent.id}")

    elif event.type == 'payment_method.attached':
        payment_method = event.data.object

        # 1. Save payment method for future use (if using Stripe Customers)
        # 2. Update customer's default payment method
        # 3. Log for customer payment preferences analytics

        print(f"Payment method attached for future use: {payment_method.id}")

    else:
        print('Unhandled event type {}'.format(event.type))

    return HttpResponse(status=200)
