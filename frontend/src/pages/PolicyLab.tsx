import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function PolicyLab() {
  const { data, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: async () => {
      const response = await axios.get('/api/policies')
      return response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700' }}>Policy Lab</h1>
        <button className="btn btn-primary">Create New Policy</button>
      </div>

      <div className="card">
        <div className="card-title">All Policies ({data?.count || 0})</div>
        <table className="table">
          <thead>
            <tr>
              <th>Policy ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>Channel</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data?.policies || []).map((policy: any) => (
              <tr key={policy.id}>
                <td>{policy.id}</td>
                <td>{policy.name}</td>
                <td>
                  <span
                    style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: policy.status === 'recommended' ? '#dcfce7' : '#f3f4f6',
                      color: policy.status === 'recommended' ? '#166534' : '#374151',
                    }}
                  >
                    {policy.status || 'draft'}
                  </span>
                </td>
                <td>{(policy.channels || []).join(', ')}</td>
                <td>
                  <button className="btn btn-secondary" style={{ marginRight: '8px', padding: '6px 12px' }}>
                    View
                  </button>
                  <button className="btn btn-primary" style={{ padding: '6px 12px' }}>
                    Evaluate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
