const BASE_URL = '/api/v1';

export const api = {
  getAuthToken() {
    return localStorage.getItem('token');
  },

  setAuthToken(token) {
    localStorage.setItem('token', token);
  },

  clearAuthToken() {
    localStorage.removeItem('token');
  },

  async request(endpoint, options = {}) {
    const token = this.getAuthToken();
    const headers = {
      ...options.headers,
    };

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An unexpected error occurred' }));
      let message = 'API Request failed';
      if (typeof errorData.detail === 'string') {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map(d => (d.msg ? `${d.loc ? d.loc.join('.') : ''}: ${d.msg}` : JSON.stringify(d))).join(', ');
      } else if (errorData.detail) {
        message = JSON.stringify(errorData.detail);
      }
      throw new Error(message);
    }

    return response.json();
  },

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    const data = await res.json().catch(() => ({ detail: 'Login failed' }));
    if (!res.ok) {
      let message = data.detail || 'Login failed';
      if (Array.isArray(data.detail)) {
        message = data.detail.map(d => d.msg).join(', ');
      }
      throw new Error(message);
    }

    if (data.access_token) {
      this.setAuthToken(data.access_token);
    }
    return data;
  },

  async register(email, password, fullName, role = 'CUSTOMER') {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, role }),
    });
  },

  async getCurrentUser() {
    return this.request('/auth/me');
  },

  async createOrder(items) {
    return this.request('/orders', {
      method: 'POST',
      body: JSON.stringify({ items }),
    });
  },

  async getOrders() {
    return this.request('/orders');
  },

  async recordPackingWeight(orderId, measuredWeight, packingEvents) {
    return this.request('/packing/record-weight', {
      method: 'POST',
      body: JSON.stringify({
        order_id: orderId,
        measured_weight_grams: measuredWeight,
        seal_intact: true,
        packing_events: packingEvents,
      }),
    });
  },

  async updateDeliveryStatus(orderId, status) {
    return this.request('/deliveries/update-status', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId, delivery_status: status }),
    });
  },

  async verifyOTP(orderId, otpCode) {
    return this.request('/deliveries/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId, otp_code: otpCode }),
    });
  },

  async raiseClaim(orderId, claimItems) {
    return this.request('/claims', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId, claim_items: claimItems }),
    });
  },

  async uploadEvidence(claimId, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/claims/${claimId}/evidence`, {
      method: 'POST',
      body: formData,
    });
  },

  async getClaims() {
    return this.request('/claims');
  },

  async getClaimDetails(claimId) {
    return this.request(`/claims/${claimId}`);
  },

  async getAdminQueue() {
    return this.request('/admin/claims');
  },

  async recordDecision(claimId, decision, notes) {
    return this.request(`/admin/claims/${claimId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, decision_notes: notes }),
    });
  },

  async getAnalytics() {
    return this.request('/admin/analytics');
  },

  async getCustomerHistory(customerId) {
    return this.request(`/customers/${customerId}/history`);
  }
};
