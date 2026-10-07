import React, { useState } from 'react';
import { Package, Truck, AlertTriangle, CheckCircle, ArrowRight, ShieldCheck, Scale, KeyRound } from 'lucide-react';

export default function CustomerOrders({ orders, onCreateOrder, onRecordPacking, onVerifyOTP, onRaiseClaim, loading }) {
  const [selectedOrderForClaim, setSelectedOrderForClaim] = useState(null);
  const [claimReasons, setClaimReasons] = useState({});
  const [selectedItems, setSelectedItems] = useState({});
  const [claimTypes, setClaimTypes] = useState({});
  const [otpInputs, setOtpInputs] = useState({});

  const sampleOrderPresets = [
    {
      name: 'Standard Grocery Order (Milk, Bread, Eggs)',
      items: [
        { sku: 'SKU-MILK', item_name: 'Organic Whole Milk 1L', quantity: 1, unit_price: 3.50, expected_weight_grams: 1000.0 },
        { sku: 'SKU-BREAD', item_name: 'Whole Wheat Sandwich Bread', quantity: 1, unit_price: 2.50, expected_weight_grams: 400.0 },
        { sku: 'SKU-EGGS', item_name: 'Grade A Large Eggs 12pk', quantity: 1, unit_price: 4.20, expected_weight_grams: 650.0 }
      ]
    },
    {
      name: 'Electronics & Accessories Order (Headphones, Charger)',
      items: [
        { sku: 'SKU-HEADPHONES', item_name: 'Wireless ANC Headphones', quantity: 1, unit_price: 89.99, expected_weight_grams: 350.0 },
        { sku: 'SKU-CHARGER', item_name: '65W USB-C Fast Charger', quantity: 1, unit_price: 29.99, expected_weight_grams: 150.0 }
      ]
    }
  ];

  const handleToggleItem = (itemId) => {
    setSelectedItems(prev => ({ ...prev, [itemId]: !prev[itemId] }));
  };

  const handleClaimTypeChange = (itemId, type) => {
    setClaimTypes(prev => ({ ...prev, [itemId]: type }));
  };

  const handleReasonChange = (itemId, reason) => {
    setClaimReasons(prev => ({ ...prev, [itemId]: reason }));
  };

  const handleSubmitClaim = (orderId) => {
    const claimItems = [];
    Object.keys(selectedItems).forEach(itemId => {
      if (selectedItems[itemId]) {
        claimItems.push({
          order_item_id: itemId,
          claim_type: claimTypes[itemId] || 'MISSING_ITEM',
          claimed_quantity: 1,
          customer_reason: claimReasons[itemId] || 'Customer reported item missing/disputed'
        });
      }
    });

    if (claimItems.length === 0) {
      alert('Please select at least one item to raise a claim.');
      return;
    }

    onRaiseClaim(orderId, claimItems);
    setSelectedOrderForClaim(null);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-600" />
            <span>Customer Orders & Claim Pipeline</span>
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Place order, simulate warehouse packing scans & exit scale weighing, verify delivery OTP, and lodge item-level claims.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {sampleOrderPresets.map((preset, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => onCreateOrder(preset.items)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <span>Place Demo Order #{idx + 1}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ))}
        </div>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-2xl border border-slate-200 text-slate-400">
          <Package className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <p className="font-medium text-slate-600">No orders placed yet.</p>
          <p className="text-sm mt-1">Click "Place Demo Order #1" above to start testing the evidence pipeline!</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {orders.map(order => (
            <div key={order.id} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-800 text-base">{order.order_number}</span>
                    <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-full border border-blue-200">
                      Status: {order.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Placed: {new Date(order.created_at).toLocaleString()} | Total: ${order.total_amount.toFixed(2)}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onRecordPacking(order)}
                    className="text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1"
                    title="Simulate warehouse scan & exit scale weigh-in"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>Simulate Warehouse Pack</span>
                  </button>

                  <div className="flex items-center gap-1 bg-amber-50 border border-amber-200 px-2 py-1 rounded-lg">
                    <KeyRound className="w-3.5 h-3.5 text-amber-600" />
                    <input
                      type="text"
                      placeholder="OTP Code"
                      value={otpInputs[order.id] || ''}
                      onChange={(e) => setOtpInputs({ ...otpInputs, [order.id]: e.target.value })}
                      className="w-16 text-xs px-1 py-0.5 border border-amber-300 rounded bg-white"
                    />
                    <button
                      onClick={() => onVerifyOTP(order.id, otpInputs[order.id])}
                      className="text-xs bg-amber-600 hover:bg-amber-700 text-white px-2 py-0.5 rounded font-medium"
                    >
                      Verify
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Order Line Items</h4>
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden mb-4">
                  {order.items.map(item => (
                    <div key={item.id} className="p-3 bg-slate-50/50 flex items-center justify-between text-sm">
                      <div>
                        <div className="font-semibold text-slate-700">{item.item_name}</div>
                        <div className="text-xs text-slate-400">SKU: {item.sku} | Qty: {item.quantity} | Weight: {item.expected_weight_grams}g</div>
                      </div>
                      <div className="font-medium text-slate-600">${(item.unit_price * item.quantity).toFixed(2)}</div>
                    </div>
                  ))}
                </div>

                {selectedOrderForClaim === order.id ? (
                  <div className="bg-slate-50 p-4 rounded-xl border border-blue-200 space-y-4">
                    <h4 className="font-semibold text-sm text-slate-800 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      <span>Select Disputed Items for Claim Submission</span>
                    </h4>

                    {order.items.map(item => (
                      <div key={item.id} className="p-3 bg-white rounded-lg border border-slate-200 space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer font-medium text-sm text-slate-700">
                          <input
                            type="checkbox"
                            checked={!!selectedItems[item.id]}
                            onChange={() => handleToggleItem(item.id)}
                            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span>{item.item_name} (SKU: {item.sku})</span>
                        </label>

                        {selectedItems[item.id] && (
                          <div className="pl-6 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                            <div>
                              <label className="block text-slate-500 mb-1">Claim Category</label>
                              <select
                                value={claimTypes[item.id] || 'MISSING_ITEM'}
                                onChange={(e) => handleClaimTypeChange(item.id, e.target.value)}
                                className="w-full p-2 border border-slate-300 rounded-md bg-slate-50"
                              >
                                <option value="MISSING_ITEM">1. Missing Item</option>
                                <option value="WRONG_ITEM">2. Wrong Item Received</option>
                                <option value="WRONG_QUANTITY">3. Wrong Quantity</option>
                                <option value="DAMAGED_ITEM">4. Damaged Product</option>
                                <option value="EXPIRED_ITEM">5. Expired Item</option>
                              </select>
                            </div>
                            <div>
                              <label className="block text-slate-500 mb-1">Reason / Description</label>
                              <input
                                type="text"
                                placeholder="Describe problem (e.g. Item missing from sealed bag)"
                                value={claimReasons[item.id] || ''}
                                onChange={(e) => handleReasonChange(item.id, e.target.value)}
                                className="w-full p-2 border border-slate-300 rounded-md"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}

                    <div className="flex justify-end gap-2 pt-2">
                      <button
                        onClick={() => setSelectedOrderForClaim(null)}
                        className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleSubmitClaim(order.id)}
                        className="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow transition"
                      >
                        Submit Item Claim
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setSelectedOrderForClaim(order.id)}
                    className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl border border-slate-300 transition flex items-center justify-center gap-1.5"
                  >
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <span>Raise Post-Delivery Claim on this Order</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
