// static/main.js

console.log("Sanity check!");

// new
// Get Stripe publishable key
fetch("/config/")
.then((result) => { return result.json(); })
.then((data) => {
  console.log("Stripe config data:", data);

  // `data.publicKey` : We'll then use this key to create a new instance of Stripe.js.

  // 1. Get Publishable Key
  // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);

  // 2. Create Checkout Session
  // Event handler
  document.querySelector("#submitBtn").addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("/create-checkout-session/")
    .then((result) => { return result.json(); })
    .then((data) => {
      console.log("Stripe checkout session data:", data);
      // Redirect to Stripe Checkout [Not supported anymore]
      // return stripe.redirectToCheckout({sessionId: data.sessionId})
      window.location.href = data.sessionUrl;
    })
    .then((res) => {
      console.log(res);
    });
  });
});
