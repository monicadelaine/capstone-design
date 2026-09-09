import axios from 'axios';

const API_BASE_URL = '/api/v1';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setToken(token) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken() {
    delete this.client.defaults.headers.common['Authorization'];
  }

  async getProfile() {
    const response = await this.client.get('/profile/');
    return response.data;
  }

  async createProfile(data) {
    const response = await this.client.post('/profile/', data);
    return response.data;
  }

  async updateProfile(data) {
    const response = await this.client.put('/profile/', data);
    return response.data;
  }

  async getProjectsBySponsor(sponsorId, semesterId = null) {
    let url = `/sponsors/${sponsorId}/projects/`;
    if (semesterId) {
      url += `?semester_id=${semesterId}`;
    }
    const response = await this.client.get(url);
    return response.data;
  }

  async createProject(data) {
    const response = await this.client.post('/projects/', data);
    return response.data;
  }
  async putProject(data, projectId) {
    const response = await this.client.put(`/projects/${projectId}/`, data);
    return response.data;
  }

  async getCurrentSemester() {
    const response = await this.client.get('/semesters/current');
    return response.data;
  }

  async getSemesters() {
    const response = await this.client.get('/semesters/');
    return response.data;
  }

  async createFeedback(data) {
    const response = await this.client.post('/feedback/', data);
    return response.data;
  }

  async getStudent(studentId) {
    const response = await this.client.get(`/students/${studentId}/`);
    const data = response.data;
    if (!data) return null;
    // Return minimal student info to avoid exposing unnecessary PII
    return {
      id: data.id ?? studentId,
      first_name: data.first_name ?? null,
      last_name: data.last_name ?? null,
      name: (data.first_name || data.last_name) ? `${data.first_name || ''}${data.first_name && data.last_name ? ' ' : ''}${data.last_name || ''}`.trim() : null
    };
  }

  async getStudents(studentIds = []) {
    // Fetch students in parallel and return a map id -> minimal student info (names only)
    const unique = Array.from(new Set(studentIds.filter(Boolean)));
    const results = await Promise.all(unique.map(id => this.getStudent(id).catch(() => null)));
    const map = {};
    unique.forEach((id, idx) => { map[String(id)] = results[idx]; });
    return map;
  }
}

export const apiService = new ApiService();
export default apiService;
