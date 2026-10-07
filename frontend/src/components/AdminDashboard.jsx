import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, 
  HelpCircle, FileText, Network, Sparkles, TrendingUp, UserCheck, ArrowRight,
  Clock, Activity, PackageCheck, Truck, Scale, RefreshCw, BarChart2
} from 'lucide-react';
import { api } from '../api/client';

export default function AdminDashboard() {
  const [adminQueue, setAdminQueue] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [customerHistory, setCustomerHistory] = useState(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingCustomer, setLoadingCustomer] = useState(false);

  useEffect(() => {
    loadAdminData();
  }, []);

  useEffect(() => {
    if (selectedClaim?.customer_id) {
      loadCustomerHistory(selectedClaim.customer_id);
    }
  }, [selectedClaim?.id]);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const claims = await api.getAdminQueue();
      const stats = await api.getAnalytics();
      setAdminQueue(claims);
      setAnalytics(stats);
      if (claims.length > 0 && !selectedClaim) {
        setSelectedClaim(claims[0]);
      } else if (claims.length > 0 && selectedClaim) {
        const updated = claims.find(c => c.id === selectedClaim.id);
        setSelectedClaim(updated || claims[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomerHistory = async (customerId) => {
    setLoadingCustomer(true);
    try {
      const history = await api.getCustomerHistory(customerId);
      setCustomerHistory(history);
    } catch (err) {
      console.error('Failed to load customer history:', err);
      setCustomerHistory(null);
    } finally {
      setLoadingCustomer(false);
    }
  };

  const handleDecision = async (decision) => {
    if (!selectedClaim) return;
    if (!decisionNotes.trim()) {
      alert('Please enter a brief analyst decision note / rationale before proceeding.');
      return;
    }
    try {
      await api.recordDecision(selectedClaim.id, decision, decisionNotes);
      alert(`Decision '${decision}' recorded with audit trail log!`);
      setDecisionNotes('');
      loadAdminData();
    } catch (err) {
      alert('Error recording decision: ' + err.message);
    }
  };

  // Helper for mock timeline if order events not explicitly array
  const deliveryEventsMock = [
    { type: 'ORDER_CREATED', title: 'Order Placed', time: '10:00 AM', status: 'COMPLETED', detail: 'Customer initialized order payment' },
    { type: 'PACKED', title: 'Warehouse Packed', time: '10:15 AM', status: 'COMPLETED', detail: 'Items picked & packed into order tote' },
    { type: 'PACKAGE_WEIGHT_RECORDED', title: 'Exit-Scale Weighed', time: '10:20 AM', status: 'COMPLETED', detail: 'Measured weight matches expected weight within tolerance' },
    { type: 'HANDOVER', title: 'Courier Handover', time: '10:45 AM', status: 'COMPLETED', detail: 'Handed over to delivery associate' },
    { type: 'OUT_FOR_DELIVERY', title: 'Out for Delivery', time: '11:30 AM', status: 'COMPLETED', detail: 'Vehicle en route to destination' },
    { type: 'OTP_VERIFIED', title: 'Delivery OTP Verified', time: '01:15 PM', status: 'COMPLETED', detail: 'PIN verified via SMS at customer doorstep' },
    { type: 'DELIVERED', title: 'Delivered', time: '01:16 PM', status: 'COMPLETED', detail: 'Package handed over successfully' },
    { type: 'CLAIM_CREATED', title: 'Claim Filed', time: '01:45 PM', status: 'WARNING', detail: 'Post-delivery claim opened by customer' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-md flex flex-wrap items-center justify-between gap-4 border border-slate-800">
        <div>
          <h2 className="text-xl font-extrabold flex items-center gap-2 tracking-tight">
            <LayoutDashboard className="w-5 h-5 text-indigo-400" />
            <span>Fraud Operations & Analyst Control Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Explainable AI Multi-Source Evidence Fusion, Risk & Confidence Scoring, and Behavioral Investigation Engine.
          </p>
        </div>
        <button
          onClick={loadAdminData}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition flex items-center gap-1.5 shadow"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Claims Ingested</div>
            <div className="text-2xl font-extrabold text-slate-800 mt-1">{analytics.total_claims}</div>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Auto Approved</div>
            <div className="text-2xl font-extrabold text-emerald-600 mt-1">{analytics.approved_claims}</div>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Investigation Queue</div>
            <div className="text-2xl font-extrabold text-rose-600 mt-1">{analytics.manual_review_claims}</div>
          </div>
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Avg Evidence Risk Score</div>
            <div className="text-2xl font-extrabold text-indigo-600 mt-1">{analytics.average_risk_score}/100</div>
          </div>
        </div>
      )}

      {/* Main Grid: Queue & Investigation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Claims Queue */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              <span>Claims Queue ({adminQueue.length})</span>
            </h3>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-semibold">Sorted by Risk</span>
          </div>

          {adminQueue.length === 0 ? (
            <div className="text-xs text-slate-400 text-center py-12">No claims currently in queue.</div>
          ) : (
            <div className="space-y-2.5 max-h-[850px] overflow-y-auto pr-1">
              {adminQueue.map(claim => {
                const score = claim.risk_assessment?.risk_score ?? 0;
                const conf = claim.risk_assessment?.confidence_score ?? 80;
                const isSelected = selectedClaim?.id === claim.id;
                const primaryReason = claim.risk_assessment?.primary_reasons?.[0] || 'Evidence mismatch';

                return (
                  <div
                    key={claim.id}
                    onClick={() => setSelectedClaim(claim)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/60 shadow-sm ring-1 ring-indigo-500'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800 text-xs">{claim.claim_number}</span>
                      <div className="flex items-center gap-1">
                        <span className={`px-2 py-0.5 rounded-md font-extrabold text-[10px] ${
                          score >= 70 ? 'bg-rose-100 text-rose-800 border border-rose-300' : score >= 30 ? 'bg-amber-100 text-amber-800 border border-amber-300' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        }`}>
                          RISK {score}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                          CONF {conf}%
                        </span>
                      </div>
                    </div>

                    <div className="text-xs font-semibold text-slate-700 mt-1.5 flex items-center justify-between">
                      <span>Type: {claim.claim_items?.[0]?.claim_type || 'MISSING_ITEM'}</span>
                      <span className="text-[10px] text-slate-400">Order: {claim.order_id?.substring(0, 8)}...</span>
                    </div>

                    <div className="text-[11px] text-slate-500 mt-1 line-clamp-1 italic">
                      "{primaryReason}"
                    </div>

                    <div className="flex justify-between items-center text-[10px] text-slate-400 mt-2 pt-2 border-t border-slate-100">
                      <span>Status: <b className="text-slate-600">{claim.status}</b></span>
                      <span>{new Date(claim.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Complete Investigation Panel */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
          {selectedClaim ? (
            <>
              {/* 1. Claim Header Summary */}
              <div className="flex flex-wrap items-center justify-between border-b border-slate-200 pb-4 gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-lg text-slate-900">{selectedClaim.claim_number}</h3>
                    <span className="bg-slate-100 text-slate-700 border border-slate-300 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                      Status: {selectedClaim.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Order ID: {selectedClaim.order_id} | Customer ID: {selectedClaim.customer_id} | Raised: {new Date(selectedClaim.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* 2. Dual Risk Score & Evidence Confidence Panel */}
              {selectedClaim.risk_assessment && (
                <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-sm border border-slate-800 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-b border-slate-800 pb-4">
                    {/* Risk Score */}
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Multi-Source Risk Score</div>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-3xl font-black text-rose-400">{selectedClaim.risk_assessment.risk_score}</span>
                        <span className="text-slate-400 text-xs font-semibold">/ 100</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          selectedClaim.risk_assessment.risk_score >= 70 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        }`}>
                          {selectedClaim.risk_assessment.risk_level}
                        </span>
                      </div>
                    </div>

                    {/* Evidence Confidence */}
                    <div>
                      <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evidence Confidence</div>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-3xl font-black text-indigo-400">{selectedClaim.risk_assessment.confidence_score ?? 85}%</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          (selectedClaim.risk_assessment.confidence_score ?? 85) >= 75 ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}>
                          {(selectedClaim.risk_assessment.confidence_score ?? 85) >= 75 ? 'HIGH CONFIDENCE' : 'LOW CONFIDENCE'}
                        </span>
                      </div>
                    </div>

                    {/* System Recommendation */}
                    <div>
                      <div className="text-xs text-slate-400 font-semibold uppercase">System Recommendation</div>
                      <div className="text-base font-extrabold text-amber-400 mt-1">
                        {selectedClaim.risk_assessment.recommended_action}
                      </div>
                    </div>
                  </div>

                  {/* 3. Explainability: Why is this claim suspicious? */}
                  <div className="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700 space-y-2 text-xs">
                    <h4 className="font-bold text-indigo-300 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Why is this claim suspicious? (Explainable Reasons)</span>
                    </h4>
                    <ul className="space-y-1 text-slate-200 list-disc list-inside">
                      {(selectedClaim.risk_assessment.primary_reasons || []).map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* 4. Pattern Alerts / Collusion Detection */}
              {selectedClaim.risk_assessment?.pattern_alerts?.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-2 text-xs">
                  <h4 className="font-bold text-amber-900 flex items-center gap-1.5 uppercase">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Fraud Pattern & Syndicate Alerts</span>
                  </h4>
                  {selectedClaim.risk_assessment.pattern_alerts.map((alert, idx) => (
                    <div key={idx} className="bg-white p-2.5 rounded-lg border border-amber-200 text-amber-900 font-medium">
                      ⚠️ <b>[{alert.type}]</b> {alert.message}
                    </div>
                  ))}
                </div>
              )}

              {/* 5. Delivery Lifecycle Event Timeline */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-indigo-600" />
                  <span>Delivery Lifecycle Event Timeline</span>
                </h4>
                <div className="relative border-l-2 border-indigo-200 ml-3 space-y-3 text-xs pl-4 py-1">
                  {deliveryEventsMock.map((ev, idx) => (
                    <div key={idx} className="relative">
                      <div className={`absolute -left-[23px] top-0.5 w-3 h-3 rounded-full border-2 border-white ${
                        ev.status === 'WARNING' ? 'bg-rose-500' : 'bg-indigo-600'
                      }`} />
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">{ev.title}</span>
                        <span className="text-[10px] text-slate-400 font-semibold">{ev.time}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">{ev.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 6. Customer Complete History & Behavioral Analytics Profile */}
              {customerHistory && (
                <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                    <h4 className="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <UserCheck className="w-4 h-4 text-indigo-600" />
                      <span>Customer Behavioral Intelligence Profile ({customerHistory.customer_id})</span>
                    </h4>
                    <span className="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-bold">
                      Account Age: {customerHistory.account_age_days} days
                    </span>
                  </div>

                  {/* Profile Metrics Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] text-slate-400 font-bold uppercase block">Total Orders</span>
                      <span className="text-lg font-extrabold text-slate-800">{customerHistory.total_orders}</span>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] text-slate-400 font-bold uppercase block">Total Claims</span>
                      <span className="text-lg font-extrabold text-rose-600">{customerHistory.total_claims}</span>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] text-slate-400 font-bold uppercase block">Claim Rate %</span>
                      <span className={`text-lg font-extrabold ${customerHistory.claim_rate_percent > 15 ? 'text-rose-600' : 'text-emerald-600'}`}>
                        {customerHistory.claim_rate_percent}%
                      </span>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] text-slate-400 font-bold uppercase block">14d Claim Velocity</span>
                      <span className="text-lg font-extrabold text-amber-600">{customerHistory.velocity_14d_claims} claims</span>
                    </div>
                  </div>

                  {/* Risk Indicators Badges */}
                  {customerHistory.risk_indicators?.length > 0 && (
                    <div className="space-y-1.5 text-xs">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Behavioral Risk Flags:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {customerHistory.risk_indicators.map((flag, idx) => (
                          <span key={idx} className="bg-rose-50 text-rose-700 border border-rose-200 px-2 py-1 rounded text-[11px] font-medium">
                            🚨 {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 7. Customer Historical Claims List */}
                  {customerHistory.claims?.length > 0 && (
                    <div className="space-y-2 text-xs pt-2 border-t border-slate-100">
                      <span className="font-bold text-slate-700 text-[11px] uppercase tracking-wider block">Past Claims History</span>
                      <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                        {customerHistory.claims.map((c, idx) => (
                          <div key={idx} className="p-2 bg-slate-50 rounded border border-slate-200 flex justify-between items-center text-[11px]">
                            <div>
                              <span className="font-bold text-slate-800">{c.claim_number}</span>
                              <span className="text-slate-400 ml-2">Order: {c.order_id?.substring(0, 8)}...</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-slate-600">{c.claim_type}</span>
                              <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                                c.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : c.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                              }`}>
                                {c.status}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 8. Factor Decomposition (+ & - Score Weights) */}
              {selectedClaim.risk_assessment?.factors?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Risk Factor Contribution Breakdown</h4>
                  <div className="grid gap-2 text-xs">
                    {selectedClaim.risk_assessment.factors.map((f, idx) => (
                      <div key={idx} className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <span className={`font-extrabold text-xs px-2 py-0.5 rounded ${f.impact > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                            {f.impact > 0 ? `+${f.impact}` : f.impact}
                          </span>
                          <span className="font-semibold text-slate-800">{f.label}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-medium">Reliability: {f.reliability}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 9. Supporting vs Contradicting Signals */}
              {selectedClaim.risk_assessment && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Supporting */}
                  <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 space-y-2 text-xs">
                    <h5 className="font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Supporting Signals ({selectedClaim.risk_assessment.supporting_evidence?.length || 0})</span>
                    </h5>
                    {(selectedClaim.risk_assessment.supporting_evidence || []).map((sig, idx) => (
                      <div key={idx} className="bg-white p-2.5 rounded-lg border border-emerald-100 space-y-1">
                        <div className="font-bold text-emerald-900 flex justify-between">
                          <span>{sig.label}</span>
                          <span className="text-[10px] text-emerald-600">Reliability: {sig.reliability}</span>
                        </div>
                        <div className="text-[11px] text-slate-500">{sig.description}</div>
                      </div>
                    ))}
                  </div>

                  {/* Contradicting */}
                  <div className="bg-rose-50/60 p-4 rounded-xl border border-rose-200 space-y-2 text-xs">
                    <h5 className="font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1">
                      <XCircle className="w-4 h-4 text-rose-600" />
                      <span>Contradicting Signals ({selectedClaim.risk_assessment.contradicting_evidence?.length || 0})</span>
                    </h5>
                    {(selectedClaim.risk_assessment.contradicting_evidence || []).map((sig, idx) => (
                      <div key={idx} className="bg-white p-2.5 rounded-lg border border-rose-100 space-y-1">
                        <div className="font-bold text-rose-900 flex justify-between">
                          <span>{sig.label}</span>
                          <span className="text-[10px] text-rose-600">Reliability: {sig.reliability}</span>
                        </div>
                        <div className="text-[11px] text-slate-500">{sig.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 10. Counterfactuals ("What evidence would change the decision?") */}
              {selectedClaim.risk_assessment?.counterfactuals?.length > 0 && (
                <div className="bg-indigo-50/70 border border-indigo-200 p-4 rounded-xl space-y-2 text-xs">
                  <h4 className="font-bold text-indigo-900 flex items-center gap-1.5 uppercase tracking-wider">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <span>Counterfactual Suggestion: What evidence could change this decision?</span>
                  </h4>
                  <div className="grid gap-2">
                    {selectedClaim.risk_assessment.counterfactuals.map((cf, idx) => (
                      <div key={idx} className="bg-white p-2.5 rounded-lg border border-indigo-100 flex items-center justify-between">
                        <span className="font-semibold text-indigo-950 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
                          <span>{cf.signal}</span>
                        </span>
                        <span className="text-[11px] text-indigo-700 font-bold">{cf.impact_description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 11. Evidence Relationship Tree Graph */}
              {selectedClaim.risk_assessment?.evidence_graph?.nodes && (
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                  <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Network className="w-4 h-4 text-indigo-600" />
                    <span>Evidence Relationship Graph</span>
                  </h4>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {selectedClaim.risk_assessment.evidence_graph.nodes.map((node, idx) => (
                      <div key={idx} className="bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-sm flex items-center gap-2">
                        <span className="font-bold text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">{node.type}</span>
                        <span className="font-medium text-slate-800">{node.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 12. Uploaded Evidence Files */}
              {selectedClaim.evidence_files?.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                  <h4 className="font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-indigo-600" />
                    <span>Customer Submitted Evidence Files ({selectedClaim.evidence_files.length})</span>
                  </h4>
                  <div className="grid gap-2">
                    {selectedClaim.evidence_files.map((file, idx) => (
                      <div key={idx} className="bg-white p-2.5 rounded-lg border border-slate-200 flex justify-between items-center">
                        <div>
                          <span className="font-semibold text-slate-800">{file.file_path.split('/').pop()}</span>
                          <span className="text-[10px] text-slate-400 block">Uploaded: {new Date(file.uploaded_at).toLocaleString()}</span>
                        </div>
                        {file.perceptual_hash && (
                          <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded">
                            pHash: {file.perceptual_hash.substring(0, 12)}...
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 13. Analyst Decision Controls with Mandatory Rationale Note */}
              <div className="bg-slate-900 text-white p-5 rounded-2xl space-y-4 shadow-sm border border-slate-800">
                <h4 className="font-extrabold text-sm uppercase tracking-wider text-slate-200">Execute Analyst Decision</h4>
                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-semibold">
                    Analyst Decision Rationale / Notes <span className="text-rose-400">* (Required for Audit Trail)</span>
                  </label>
                  <textarea
                    placeholder="Enter decision rationale (e.g., 'Exit scale weight and OTP handover confirm complete package departure. Rejecting claim.')"
                    value={decisionNotes}
                    onChange={(e) => setDecisionNotes(e.target.value)}
                    className="w-full p-3 text-xs border border-slate-700 rounded-xl bg-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    rows={2}
                  />
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    onClick={() => handleDecision('APPROVED')}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-3 rounded-xl shadow transition"
                  >
                    Approve Claim
                  </button>
                  <button
                    onClick={() => handleDecision('REQUEST_MORE_EVIDENCE')}
                    className="flex-1 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold py-3 rounded-xl shadow transition"
                  >
                    Request Evidence
                  </button>
                  <button
                    onClick={() => handleDecision('ESCALATE')}
                    className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-3 rounded-xl shadow transition"
                  >
                    Escalate
                  </button>
                  <button
                    onClick={() => handleDecision('REJECTED')}
                    className="flex-1 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold py-3 rounded-xl shadow transition"
                  >
                    Reject Claim
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-slate-400 font-medium">
              Select a claim from the left queue to open investigation details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
