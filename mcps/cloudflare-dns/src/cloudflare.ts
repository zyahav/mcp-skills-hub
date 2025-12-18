import axios, { AxiosInstance } from 'axios';

export interface DNSRecord {
  id: string;
  type: string;
  name: string;
  content: string;
  proxied: boolean;
  ttl: number;
}

export interface CreateRecordParams {
  type: string;
  name: string;
  content: string;
  proxied?: boolean;
  ttl?: number;
  comment?: string;
}

export interface UpdateRecordParams {
  type: string;
  name: string;
  content: string;
  proxied?: boolean;
  ttl?: number;
  comment?: string;
}

const ZONE_DOMAIN = 'zurielyahav.com';

export class CloudflareClient {
  private api: AxiosInstance;

  constructor(private apiToken: string, private zoneId: string) {
    this.api = axios.create({
      baseURL: 'https://api.cloudflare.com/client/v4',
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Convert subdomain to FQDN for Cloudflare API queries
   */
  private toFQDN(subdomain: string): string {
    if (subdomain.endsWith(ZONE_DOMAIN)) {
      return subdomain;
    }
    return `${subdomain}.${ZONE_DOMAIN}`;
  }

  async listRecords(subdomain?: string, type?: string): Promise<DNSRecord[]> {
    const params: any = {};
    if (subdomain) params.name = this.toFQDN(subdomain);
    if (type) params.type = type;

    try {
      const response = await this.api.get(`/zones/${this.zoneId}/dns_records`, { params });
      if (!response.data.success) {
        throw new Error(`Cloudflare API Error: ${JSON.stringify(response.data.errors)}`);
      }
      return response.data.result;
    } catch (error: any) {
      throw new Error(`Failed to list records: ${error.message}`);
    }
  }


  async createRecord(record: CreateRecordParams): Promise<DNSRecord> {
    try {
      const response = await this.api.post(`/zones/${this.zoneId}/dns_records`, record);
      if (!response.data.success) {
        throw new Error(`Cloudflare API Error: ${JSON.stringify(response.data.errors)}`);
      }
      return response.data.result;
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Failed to create record: ${JSON.stringify(error.response.data)}`);
      }
      throw new Error(`Failed to create record: ${error.message}`);
    }
  }

  async updateRecord(id: string, record: UpdateRecordParams): Promise<DNSRecord> {
    try {
      const response = await this.api.put(`/zones/${this.zoneId}/dns_records/${id}`, record);
      if (!response.data.success) {
        throw new Error(`Cloudflare API Error: ${JSON.stringify(response.data.errors)}`);
      }
      return response.data.result;
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Failed to update record: ${JSON.stringify(error.response.data)}`);
      }
      throw new Error(`Failed to update record: ${error.message}`);
    }
  }

  async deleteRecord(id: string): Promise<void> {
    try {
      const response = await this.api.delete(`/zones/${this.zoneId}/dns_records/${id}`);
      if (!response.data.success) {
        throw new Error(`Cloudflare API Error: ${JSON.stringify(response.data.errors)}`);
      }
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Failed to delete record: ${JSON.stringify(error.response.data)}`);
      }
      throw new Error(`Failed to delete record: ${error.message}`);
    }
  }
}
