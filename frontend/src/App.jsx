import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import CustomerOrders from './components/CustomerOrders';
import ClaimStatusView from './components/ClaimStatusView';
import AdminDashboard from './components/AdminDashboard';
import { api } from './api/client';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('orders');
  const [orders, setOrders] = useState([]);
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      let user = await api.getCurrentUser().catch(() => null);
      if (!user) {
        // Try logging in first
        const loginData = await api.login('customer@demo.com', 'Password123!').catch(() => null);
        if (loginData?.user) {
          user = loginData.user;
        } else {
          // If login fails, register and login
          await api.register('customer@demo.com', 'Password123!', 'Demo Customer', 'CUSTOMER').catch(() => {});
          const res = await api.login('customer@demo.com', 'Password123!').catch(() => null);
          user = res?.user;
        }
      }
      setCurrentUser(user);
      if (user) {
        await loadCustomerData();
      }
    } catch (err) {
      console.error("Init app error:", err);
    }
  };

  const loadCustomerData = async () => {
    setLoading(true);
    try {
      const orderList = await api.getOrders().catch(() => []);
      const claimList = await api.getClaims().catch(() => []);
      setOrders(orderList);
      setClaims(claimList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchRole = async (role) => {
    const email = role === 'ADMIN' ? 'admin@demo.com' : 'customer@demo.com';
    const name = role === 'ADMIN' ? 'Demo Fraud Analyst' : 'Demo Customer';
    
    await api.register(email, 'Password123!', name, role).catch(() => {});
    const loginData = await api.login(email, 'Password123!');
    setCurrentUser(loginData.user);
    loadCustomerData();
    if (role === 'ADMIN') {
      setActiveTab('admin');
    } else {
      setActiveTab('orders');
    }
  };

  const handleLogout = () => {
    api.clearAuthToken();
    setCurrentUser(null);
  };

  const handleCreateOrder = async (items) => {
    setLoading(true);
    try {
      if (!currentUser) {
        await initApp();
      }
      await api.createOrder(items);
      await loadCustomerData();
    } catch (err) {
      // If unauthorized, retry login once
      if (err.message.includes('Could not validate') || err.message.includes('Unauthorized') || err.message.includes('Not authenticated')) {
        try {
          await initApp();
          await api.createOrder(items);
          await loadCustomerData();
          return;
        } catch (retryErr) {
          alert('Error creating order: ' + retryErr.message);
          return;
        }
      }
      alert('Error creating order: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPacking = async (order) => {
    try {
      const packingEvents = order.items.map(item => ({
        sku: item.sku,
        scanned: true,
        station_id: 'STATION-01'
      }));

      const totalExpected = order.items.reduce((sum, item) => sum + (item.expected_weight_grams * item.quantity), 0);

      await api.recordPackingWeight(order.id, totalExpected, packingEvents);
      alert(`Warehouse scan completed & exit scale weight recorded (${totalExpected}g)!`);
      loadCustomerData();
    } catch (err) {
      alert('Error recording packing: ' + err.message);
    }
  };

  const handleVerifyOTP = async (orderId, otpCode) => {
    if (!otpCode) {
      alert('Please enter the delivery OTP code!');
      return;
    }
    try {
      await api.verifyOTP(orderId, otpCode);
      alert('Delivery OTP Verified successfully!');
      loadCustomerData();
    } catch (err) {
      alert('OTP Verification Failed: ' + err.message);
    }
  };

  const handleRaiseClaim = async (orderId, claimItems) => {
    setLoading(true);
    try {
      await api.raiseClaim(orderId, claimItems);
      alert('Claim submitted and evaluated by Evidence Fusion Engine!');
      loadCustomerData();
      setActiveTab('claims');
    } catch (err) {
      alert('Error submitting claim: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadEvidence = async (claimId, file) => {
    try {
      await api.uploadEvidence(claimId, file);
      alert('Evidence uploaded successfully! Fusion risk score updated.');
      loadCustomerData();
    } catch (err) {
      alert('Error uploading evidence: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      <Navbar
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
        onSwitchRole={handleSwitchRole}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'orders' && (
          <CustomerOrders
            orders={orders}
            onCreateOrder={handleCreateOrder}
            onRecordPacking={handleRecordPacking}
            onVerifyOTP={handleVerifyOTP}
            onRaiseClaim={handleRaiseClaim}
            loading={loading}
          />
        )}

        {activeTab === 'claims' && (
          <ClaimStatusView
            claims={claims}
            onUploadEvidence={handleUploadEvidence}
          />
        )}

        {activeTab === 'admin' && (
          <AdminDashboard />
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        DeliveryFraud — AI-Powered Delivery Fraud Detection & Evidence Fusion System
      </footer>
    </div>
  );
}
