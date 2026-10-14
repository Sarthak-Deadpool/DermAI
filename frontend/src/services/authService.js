import apiClient from "../api/client";

const authServices = {
    async getCsrfToken() {
        const response = await apiClient.get("/auth/csrf");
        return response.data;
    },

    async register(userData) {
        await this.getCsrfToken();
        const response = await apiClient.post("/auth/register", userData);
        return response.data;
    },

    async login(credentials) {
        await this.getCsrfToken();
        const response = await apiClient.post("/auth/login", credentials);
        return response.data;
    },

    async getCurrentUser() {
        const response = await apiClient.get("/auth/me");
        return response.data;
    },

    async logout() {
        await this.getCsrfToken();
        const response = await apiClient.post("/auth/logout");
        return response.data;
    }
}

export default authServices;