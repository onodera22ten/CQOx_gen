export default function Diagnostics() {
  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Diagnostics & Audit
      </h1>

      <div className="card">
        <div className="card-title">Causal Assurance Score (CAS)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '16px' }}>
          <div style={{ fontSize: '48px', fontWeight: '700', color: '#16a34a' }}>0.85</div>
          <div style={{ flex: 1 }}>
            <div style={{ background: '#e5e7eb', height: '24px', borderRadius: '12px', overflow: 'hidden' }}>
              <div style={{ width: '85%', height: '100%', background: 'linear-gradient(90deg, #10b981 0%, #16a34a 100%)' }}></div>
            </div>
            <p style={{ marginTop: '8px', color: '#64748b', fontSize: '14px' }}>
              Score above 0.8 indicates high confidence in causal estimates
            </p>
          </div>
        </div>
      </div>

      <div className="grid">
        <div className="card">
          <div className="card-title">Covariate Balance</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#166534', fontWeight: '700', fontSize: '20px' }}>
              ✓
            </div>
            <div>
              <div style={{ fontWeight: '600' }}>PASSED</div>
              <div style={{ fontSize: '14px', color: '#64748b' }}>Max SMD: 0.08</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Overlap / Positivity</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#166534', fontWeight: '700', fontSize: '20px' }}>
              ✓
            </div>
            <div>
              <div style={{ fontWeight: '600' }}>PASSED</div>
              <div style={{ fontSize: '14px', color: '#64748b' }}>Violation rate: 2%</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Sensitivity (Γ)</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#fef3c7', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#92400e', fontWeight: '700', fontSize: '20px' }}>
              !
            </div>
            <div>
              <div style={{ fontWeight: '600' }}>WARNING</div>
              <div style={{ fontSize: '14px', color: '#64748b' }}>Γ = 1.5 (threshold: 1.3)</div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">All Diagnostics (14 Checks)</div>
        <table className="table">
          <thead>
            <tr>
              <th>Diagnostic</th>
              <th>Status</th>
              <th>Value</th>
              <th>Threshold</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Covariate Balance (SMD)', status: 'pass', value: '0.08', threshold: '< 0.1' },
              { name: 'Overlap / Positivity', status: 'pass', value: '2%', threshold: '< 5%' },
              { name: 'Love Plot', status: 'pass', value: 'All covariates', threshold: '-' },
              { name: 'Sensitivity (Γ)', status: 'warning', value: '1.5', threshold: '> 1.3' },
              { name: 'E-value', status: 'pass', value: '2.1', threshold: '> 1.5' },
            ].map((diagnostic) => (
              <tr key={diagnostic.name}>
                <td>{diagnostic.name}</td>
                <td>
                  <span
                    style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: diagnostic.status === 'pass' ? '#dcfce7' : '#fef3c7',
                      color: diagnostic.status === 'pass' ? '#166534' : '#92400e',
                      textTransform: 'uppercase',
                      fontWeight: '600',
                    }}
                  >
                    {diagnostic.status}
                  </span>
                </td>
                <td>{diagnostic.value}</td>
                <td>{diagnostic.threshold}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
