export default function PricingPage({ onNavigate }) {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      tokens: 25,
      features: [
        '25 transcripts per month',
        'Basic transcript extraction',
        'Copy & download',
        'Community support'
      ],
      cta: 'Get Started',
      popular: false
    },
    {
      name: 'Plus',
      price: '$9.99',
      period: 'per month',
      tokens: 1000,
      features: [
        '1,000 transcripts per month',
        'Podcast generation',
        'Multiple voice options',
        'API access',
        'Priority support',
        'Export in multiple formats'
      ],
      cta: 'Upgrade to Plus',
      popular: true
    },
    {
      name: 'Pro',
      price: '$24.99',
      period: 'per month',
      tokens: 3000,
      features: [
        '3,000 transcripts per month',
        'Everything in Plus',
        'Advanced voice customization',
        'Bulk processing',
        'Custom API limits',
        'Dedicated support',
        'Team collaboration'
      ],
      cta: 'Upgrade to Pro',
      popular: false
    }
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Simple, Transparent Pricing</h1>
        <p>Choose the plan that works best for you</p>
      </div>

      <div className="pricing-grid">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`pricing-card ${plan.popular ? 'popular' : ''}`}
          >
            {plan.popular && <div className="popular-badge">Most Popular</div>}

            <div className="pricing-header">
              <h3>{plan.name}</h3>
              <div className="price">
                {plan.price}
                <span className="period">/{plan.period}</span>
              </div>
              <div className="tokens-badge">
                {plan.tokens} tokens/month
              </div>
            </div>

            <ul className="feature-list">
              {plan.features.map((feature, index) => (
                <li key={index}>
                  <span className="check-icon">✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            <button
              className={`btn ${plan.popular ? 'btn-primary' : 'btn-secondary'} btn-block`}
              onClick={() => onNavigate('login')}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Frequently Asked Questions</h3>

        <div className="faq-list">
          <div className="faq-item">
            <h4>What is a token?</h4>
            <p>Each transcript extraction costs 1 token. Your token count resets at the start of each billing cycle.</p>
          </div>

          <div className="faq-item">
            <h4>Can I cancel anytime?</h4>
            <p>Yes! You can cancel your subscription at any time. Your plan will remain active until the end of your billing period.</p>
          </div>

          <div className="faq-item">
            <h4>What happens if I run out of tokens?</h4>
            <p>You can upgrade to a higher plan at any time, or wait for your tokens to reset at the start of the next billing cycle.</p>
          </div>

          <div className="faq-item">
            <h4>Do unused tokens roll over?</h4>
            <p>No, unused tokens do not roll over to the next billing cycle.</p>
          </div>

          <div className="faq-item">
            <h4>Is there a free trial for paid plans?</h4>
            <p>All new users start with the Free plan, which gives you 25 tokens to try out the service.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
