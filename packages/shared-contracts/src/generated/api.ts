/**
 * source: contracts/openapi-v1.yaml
 * OpenAPI: 2.0.1-draft; generator: openapi-typescript 7.13.0
 * Generated deterministically; do not edit by hand.
 */
export interface paths {
    "/api/v1/admin/failed-questions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["listFailedQuestions"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/failed-questions/{id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["getFailedQuestion"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/failed-questions/{id}/reason": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch: operations["confirmFallbackReason"];
        trace?: never;
    };
    "/api/v1/admin/kb-candidates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["listKBCandidates"];
        put?: never;
        post: operations["createKBCandidate"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/kb-candidates/{id}/review": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch: operations["reviewKBCandidate"];
        trace?: never;
    };
    "/api/v1/admin/kb-candidates/{id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["submitKBCandidate"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/quality-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["getQualitySummary"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/chat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["createChatAnswer"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/offices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["listOffices"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["health"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["readiness"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** @enum {string} */
        CandidateStatus: "NEW" | "REASON_CONFIRMED" | "DRAFTED" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED";
        /**
         * @description SYSTEM_ERROR is represented by the HTTP 503 envelope, not a 200 ChatResponse.
         * @enum {string}
         */
        ChatAnswerStatus: "SUCCESS" | "FOLLOWUP" | "FALLBACK";
        ChatRequest: {
            /** @description Optional signed conversational context. Clients treat it as opaque and keep it only in current-tab memory. Missing, null, expired, invalid, or unsupported tokens are treated as no context, not authentication failures. The token is never a source of official facts or authority. */
            context_token?: string | null;
            question: string;
            /** @enum {string|null} */
            selected_region?: "아름동" | "도담동" | "조치원읍" | null;
            /** @default false */
            simple_language?: boolean;
        };
        ChatResponse: {
            answer_status: components["schemas"]["ChatAnswerStatus"];
            confidence?: number | null;
            /** @description Fresh signed 15-minute context for current-tab memory. SUCCESS and FOLLOWUP may return a token; FALLBACK always returns null. Never log, persist, display, or use it as authentication. */
            context_token: string | null;
            department?: string | null;
            fallback?: components["schemas"]["Fallback"] | null;
            fee?: string | null;
            followup_options?: string[];
            intent: components["schemas"]["Intent"];
            procedure_steps?: string[];
            processing_time?: string | null;
            /** Format: uuid */
            request_id: string;
            required_documents?: string[];
            sources: components["schemas"]["Source"][];
            summary?: string | null;
        } & (unknown & unknown);
        FailedQuestion: {
            candidate_eligible: boolean;
            /** Format: date-time */
            created_at: string;
            fallback_reason: components["schemas"]["StoredFailureReason"];
            /** Format: uuid */
            id: string;
            intent: components["schemas"]["Intent"];
            /** @description Null only after the 30-day text retention job has purged the field. */
            masked_question: string | null;
            status: components["schemas"]["CandidateStatus"];
            /**
             * Format: date-time
             * @description Expiry of masked_question only; exactly 30 days after creation.
             */
            text_expires_at: string;
            /**
             * Format: date-time
             * @description Actual purge time; null while masked_question is retained.
             */
            text_purged_at: string | null;
        };
        Fallback: {
            candidate_eligible: boolean;
            message: string;
            next_actions?: string[];
            office?: components["schemas"]["Office"] | null;
            reason: components["schemas"]["FallbackReason"];
            title: string;
        };
        /** @enum {string} */
        FallbackReason: "INSUFFICIENT_GROUNDING" | "PERSONAL_LOOKUP" | "LEGAL_JUDGMENT" | "OUT_OF_SCOPE";
        HealthResponse: {
            /** @constant */
            status: "ok";
        };
        /** @enum {string} */
        Intent: "MOVE_IN_RESIDENT_REGISTRATION" | "CERTIFICATE_ISSUANCE" | "BULKY_WASTE" | "LOCAL_TAX_GENERAL" | "OUT_OF_SCOPE" | "UNKNOWN";
        KBCandidateCreate: {
            answer_summary: string;
            category: components["schemas"]["Intent"];
            caution?: string | null;
            department: string;
            /** Format: uuid */
            failed_question_id: string;
            fee?: string | null;
            /** Format: date */
            last_verified_at: string;
            procedure_steps?: string[];
            processing_time?: string | null;
            /** @description Human-generalized question that must pass PII validation; not a long-term copy of masked_question. */
            representative_question: string;
            required_documents?: string[];
            source_title: string;
            /** Format: uri */
            source_url: string;
            title: string;
        };
        Office: {
            address: string;
            id: string;
            /** Format: date */
            last_verified_at: string;
            /** Format: uri */
            map_url?: string | null;
            office_name: string;
            opening_hours?: string | null;
            phone: string;
            region: string;
            source_title: string;
            /** Format: uri */
            source_url?: string;
        };
        ReadyResponse: {
            /** @constant */
            status: "ready";
        };
        ServiceUnavailableEnvelope: {
            error: {
                /** @constant */
                code: "SERVICE_UNAVAILABLE";
                message: string;
                /** Format: uuid */
                request_id: string;
                /** @constant */
                retryable: true;
            };
        };
        Source: {
            /** Format: date */
            last_verified_at: string;
            source_id: string;
            title: string;
            /** Format: uri */
            url: string;
            used_fields?: string[];
        };
        /**
         * @description OUT_OF_SCOPE never creates a failed_questions row.
         * @enum {string}
         */
        StoredFailureReason: "INSUFFICIENT_GROUNDING" | "PERSONAL_LOOKUP" | "LEGAL_JUDGMENT";
    };
    responses: {
        /** @description No safe response can be produced from approved ACTIVE KB and currently available dependencies. */
        ServiceUnavailable: {
            headers: {
                /** @description Suggested retry delay in seconds. */
                "Retry-After"?: number;
                [name: string]: unknown;
            };
            content: {
                /**
                 * @example {
                 *       "error": {
                 *         "code": "SERVICE_UNAVAILABLE",
                 *         "message": "잠시 후 다시 시도해 주세요.",
                 *         "request_id": "7d444840-9dc0-11d1-b245-5ffdce74fad2",
                 *         "retryable": true
                 *       }
                 *     }
                 */
                "application/json": components["schemas"]["ServiceUnavailableEnvelope"];
            };
        };
        /** @description Request validation error */
        ValidationError: {
            headers: {
                [name: string]: unknown;
            };
            content?: never;
        };
    };
    parameters: {
        /** @description Local/private demo actor only; not an authentication credential. */
        DemoActorId: string;
        /** @description Local/private role switch only; reject when admin routes are not privately gated. */
        DemoRole: "OPERATOR" | "APPROVER";
        IdPath: string;
    };
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    listFailedQuestions: {
        parameters: {
            query?: {
                reason?: components["schemas"]["StoredFailureReason"];
                status?: components["schemas"]["CandidateStatus"];
            };
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Masked failures only */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        items?: components["schemas"]["FailedQuestion"][];
                    };
                };
            };
            /** @description Admin route disabled or demo actor not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    getFailedQuestion: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path: {
                id: components["parameters"]["IdPath"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Failed question detail */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FailedQuestion"];
                };
            };
            /** @description Admin route disabled or demo actor not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    confirmFallbackReason: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path: {
                id: components["parameters"]["IdPath"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    reason: components["schemas"]["StoredFailureReason"];
                };
            };
        };
        responses: {
            /** @description Reason confirmed */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Admin route disabled or role not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Invalid state transition */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    listKBCandidates: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Candidate list */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Admin route disabled or demo actor not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    createKBCandidate: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KBCandidateCreate"];
            };
        };
        responses: {
            /** @description Draft candidate created */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Role not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description PII or official-source validation failed */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    reviewKBCandidate: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path: {
                id: components["parameters"]["IdPath"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    /** @enum {string} */
                    decision: "APPROVED" | "REJECTED";
                    review_comment: string;
                };
            };
        };
        responses: {
            /** @description Review applied; approval activates KB atomically */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Approver role required or self-approval blocked */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Invalid state */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    submitKBCandidate: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path: {
                id: components["parameters"]["IdPath"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Candidate pending approval */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Incomplete or wrong state */
            409: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    getQualitySummary: {
        parameters: {
            query?: never;
            header: {
                /** @description Local/private demo actor only; not an authentication credential. */
                "X-Demo-Actor-Id": components["parameters"]["DemoActorId"];
                /** @description Local/private role switch only; reject when admin routes are not privately gated. */
                "X-Demo-Role": components["parameters"]["DemoRole"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Values labeled by source: event, evaluation, or mock */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Admin route disabled or demo actor not allowed */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    createChatAnswer: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChatRequest"];
            };
        };
        responses: {
            /** @description Success, follow-up, or safe fallback */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatResponse"];
                };
            };
            422: components["responses"]["ValidationError"];
            503: components["responses"]["ServiceUnavailable"];
        };
    };
    listOffices: {
        parameters: {
            query: {
                intent: components["schemas"]["Intent"];
                region: "아름동" | "도담동" | "조치원읍";
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Official office matches */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        items: components["schemas"]["Office"][];
                    };
                };
            };
        };
    };
    health: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Process health */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponse"];
                };
            };
        };
    };
    readiness: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Required dependencies and seed data ready */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReadyResponse"];
                };
            };
            503: components["responses"]["ServiceUnavailable"];
        };
    };
}
