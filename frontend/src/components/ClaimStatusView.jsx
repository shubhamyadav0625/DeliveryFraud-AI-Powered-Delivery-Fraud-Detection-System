import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Upload, FileText, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function ClaimStatusView({ claims, onUploadEvidence }) {
  const [selectedFile, setSelectedFile] = useState({});

  const handleFileChange = (claimId, file) => {
    setSelectedFile(prev => ({ ...prev, [claimId]: file }));
  };

  const handleUpload = (claimId) => {
    const file = selectedFile[claimId];
    if (!file) {
      alert('Please select an image or document file first.');
      return;
    }
    onUploadEvidence(claimId, file);
    setSelectedFile(prev => ({ ...prev, [claimId]: null }));
  };

  const getCustomerTimelineStep = (status) => {
    switch (status) {
      case 'APPROVED':
        return 4;
      case 'REJECTED':
        return 4;
      case 'VERIFY_REQUESTED':
        return 3;
      case 'INVESTIGATION_REQUIRED':
      case 'MANUAL_REVIEW':
        return 3;
      case 'ANALYZING':
        return 2;
      default:
        return 1;
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-600" />
          <span>My Submitted Claims & Verification Progress</span>
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Track the verification progress of your claims and upload unboxing photo/video evidence.
        </p>
      </div>

      {claims.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-2xl border border-slate-200 text-slate-400">
          <ShieldAlert className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <p className="font-medium text-slate-600">No active claims found.</p>
          <p className="text-sm mt-1">Select an order in "Customer View" to lodge an item claim!</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {claims.map(claim => {
            const step = getCustomerTimelineStep(claim.status);
            return (
              <div key={claim.id} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-slate-800 text-base">{claim.claim_number}</span>
                      <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full border border-blue-200">
                        {claim.status === 'APPROVED' ? 'Approved & Refunded' : claim.status === 'REJECTED' ? 'Claim Closed' : claim.status === 'VERIFY_REQUESTED' ? 'Verification Requested' : 'Under Process'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Submitted: {new Date(claim.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  {/* Neutral Customer Timeline */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Claim Resolution Timeline</h4>
                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                      <div className={`p-2 rounded-lg border font-semibold ${step >= 1 ? 'bg-blue-50 border-blue-300 text-blue-800' : 'bg-white text-slate-400'}`}>
                        1. Claim Submitted
                      </div>
                      <div className={`p-2 rounded-lg border font-semibold ${step >= 2 ? 'bg-blue-50 border-blue-300 text-blue-800' : 'bg-white text-slate-400'}`}>
                        2. Signals Analyzed
                      </div>
                      <div className={`p-2 rounded-lg border font-semibold ${step >= 3 ? 'bg-amber-50 border-amber-300 text-amber-800' : 'bg-white text-slate-400'}`}>
                        3. Review & Verification
                      </div>
                      <div className={`p-2 rounded-lg border font-semibold ${step >= 4 ? 'bg-emerald-50 border-emerald-300 text-emerald-800' : 'bg-white text-slate-400'}`}>
                        4. Final Resolution
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Disputed Line Items</h4>
                    <div className="grid gap-2">
                      {claim.claim_items.map(item => (
                        <div key={item.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs flex justify-between items-center">
                          <div>
                            <span className="font-semibold text-slate-800">{item.claim_type}</span>
                            <span className="text-slate-500 ml-2">Description: "{item.customer_reason || 'No description'}"</span>
                          </div>
                          <span className="bg-slate-200 text-slate-700 text-[10px] font-bold px-2.5 py-0.5 rounded">
                            Disputed Qty: {item.claimed_quantity}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Upload className="w-4 h-4 text-blue-600" />
                      <div>
                        <div className="text-xs font-semibold text-slate-700">Attach Supporting Evidence Photo / Video</div>
                        <div className="text-[11px] text-slate-400">Unboxing photos help expedite manual verification.</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="file"
                        onChange={(e) => handleFileChange(claim.id, e.target.files[0])}
                        className="text-xs text-slate-500 file:mr-2 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                      <button
                        onClick={() => handleUpload(claim.id)}
                        className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg transition shadow"
                      >
                        Upload
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
