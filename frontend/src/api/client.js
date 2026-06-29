import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message
    console.error('API Error:', msg)
    err.message = msg
    return Promise.reject(err)
  },
)

export default client
