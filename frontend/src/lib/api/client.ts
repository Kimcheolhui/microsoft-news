import { PUBLIC_API_BASE_URL } from '$env/static/public';

const base = PUBLIC_API_BASE_URL;

async function fetchJson<T>(path: string): Promise<T> {
	const res = await fetch(`${base}${path}`);
	if (!res.ok) {
		throw new Error(`API error: ${res.status} ${res.statusText}`);
	}
	return res.json();
}

export interface UpdateSummary {
	id: string;
	source_id: string;
	title: string;
	title_ko: string | null;
	summary: string | null;
	summary_ko: string | null;
	source_url: string;
	published_date: string | null;
	update_type: string[] | null;
	categories: string[] | null;
	services_affected: string[] | null;
	ingested_at: string;
}

export interface ReportBrief {
	id: string;
	status: string;
	update_type: string | null;
	title_ko: string | null;
	title_en: string | null;
	summary_ko: string | null;
	summary_en: string | null;
	generated_at: string | null;
}

export interface UpdateDetail extends UpdateSummary {
	body: string | null;
	raw_data: Record<string, unknown> | null;
	report: ReportBrief | null;
}

export interface UpdateList {
	items: UpdateSummary[];
	total: number;
	page: number;
	page_size: number;
}

export interface ReportRun {
	id: string;
	step: string;
	status: string;
	started_at: string;
	finished_at: string | null;
	error: Record<string, unknown> | null;
	tokens_used: number | null;
}

export interface ReportDetail {
	id: string;
	update_id: string;
	status: string;
	update_type: string | null;
	affected_services: string[] | null;
	title_ko: string | null;
	title_en: string | null;
	summary_ko: string | null;
	summary_en: string | null;
	body_ko: string | null;
	body_en: string | null;
	analysis_data: Record<string, unknown> | null;
	related_update_ids: string[] | null;
	references: Record<string, unknown>[] | null;
	model_used: string | null;
	tokens_used: number | null;
	generated_at: string | null;
	created_at: string;
	updated_at: string;
	runs: ReportRun[];
	update_title: string | null;
	update_source_url: string | null;
}

export interface Source {
	id: string;
	name: string;
	url: string;
	source_type: string;
	enabled: boolean;
	last_scraped_at: string | null;
	created_at: string;
}

export function getUpdates(params: {
	page?: number;
	page_size?: number;
	source_id?: string;
	update_type?: string;
	q?: string;
}): Promise<UpdateList> {
	const qs = new URLSearchParams();
	if (params.page) qs.set('page', String(params.page));
	if (params.page_size) qs.set('page_size', String(params.page_size));
	if (params.source_id) qs.set('source_id', params.source_id);
	if (params.update_type) qs.set('update_type', params.update_type);
	if (params.q) qs.set('q', params.q);
	return fetchJson(`/api/v1/updates?${qs}`);
}

export function getUpdate(id: string): Promise<UpdateDetail> {
	return fetchJson(`/api/v1/updates/${id}`);
}

export function getReport(id: string): Promise<ReportDetail> {
	return fetchJson(`/api/v1/reports/${id}`);
}

export function getSources(): Promise<Source[]> {
	return fetchJson('/api/v1/sources');
}
