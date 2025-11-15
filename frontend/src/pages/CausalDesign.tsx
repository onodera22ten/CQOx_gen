export default function CausalDesign() {
  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Causal Design & Evaluation
      </h1>

      <div className="card">
        <div className="card-title">Train Causal Models</div>
        <p style={{ marginBottom: '16px', color: '#64748b' }}>
          Select dataset and features to train causal estimators
        </p>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            Dataset
          </label>
          <select style={{ width: '100%', padding: '10px', border: '1px solid #e5e7eb', borderRadius: '6px' }}>
            <option>Select a dataset...</option>
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
            Estimators
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {['S-Learner', 'T-Learner', 'X-Learner', 'DR-Learner', 'Causal Forest'].map((estimator) => (
              <label key={estimator} style={{ display: 'flex', alignItems: 'center' }}>
                <input type="checkbox" defaultChecked style={{ marginRight: '8px' }} />
                {estimator}
              </label>
            ))}
          </div>
        </div>

        <button className="btn btn-primary">Train Models</button>
      </div>

      <div className="card">
        <div className="card-title">Recent Training Runs</div>
        <table className="table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Dataset</th>
              <th>Status</th>
              <th>ATE</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>run_001</td>
              <td>dataset_2025Q1</td>
              <td>
                <span style={{ color: '#16a34a', fontWeight: '500' }}>Completed</span>
              </td>
              <td>125.5</td>
              <td>
                <button className="btn btn-secondary" style={{ padding: '6px 12px' }}>
                  View Results
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
