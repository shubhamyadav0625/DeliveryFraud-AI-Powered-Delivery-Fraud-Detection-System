import React from 'react';
import { ShieldCheck, UserCheck, ShieldAlert, LogOut, PackageSearch, LayoutDashboard } from 'lucide-react';

export default function Navbar({ currentUser, activeTab, setActiveTab, onLogout, onSwitchRole }) {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('orders')}>
          <div className="bg-gradient-to-tr from-blue-600 to-indigo-500 p-2 rounded-xl text-white shadow-lg">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="font-bold text-lg leading-tight tracking-wide bg-gradient-to-r from-blue-400 to-indigo-200 bg-clip-text text-transparent">
              DeliveryFraud
            </div>
            <div className="text-[10px] text-slate-400 tracking-wider uppercase">
              AI Evidence Fusion System
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'orders'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <PackageSearch className="w-4 h-4" />
            <span>Customer View</span>
          </button>

          <button
            onClick={() => setActiveTab('claims')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'claims'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>My Claims</span>
          </button>

          <button
            onClick={() => setActiveTab('admin')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'admin'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Fraud Analyst Dashboard</span>
          </button>
        </div>

        <div className="flex items-center space-x-3">
          {currentUser ? (
            <div className="flex items-center space-x-3 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <UserCheck className="w-4 h-4 text-blue-400" />
              <div className="text-xs">
                <div className="font-semibold text-slate-200">{currentUser.full_name}</div>
                <div className="text-[10px] text-slate-400">{currentUser.role}</div>
              </div>
              <button
                onClick={onLogout}
                className="text-slate-400 hover:text-red-400 p-1 rounded-md transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onSwitchRole('CUSTOMER')}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-md border border-slate-700 transition"
              >
                Demo Customer
              </button>
              <button
                onClick={() => onSwitchRole('ADMIN')}
                className="text-xs bg-indigo-900/60 hover:bg-indigo-800 text-indigo-200 px-3 py-1.5 rounded-md border border-indigo-700 transition"
              >
                Demo Admin
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
