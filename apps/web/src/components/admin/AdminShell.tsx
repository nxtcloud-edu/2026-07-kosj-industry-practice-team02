"use client";

/**
 * 이음센터 공통 셸 - DESIGN.md v3 §5-1 사이드바 (216px, --color-admin-nav).
 * - 브랜드: 로고 심볼 흰색 변형 + "세종 민원이음 관리자" + "이음센터".
 * - 메뉴: P0 3개 라우팅만. 활성 = 흰 배경 + admin-nav 텍스트 800.
 *   건수 뱃지(실패 질문=신규 NEW, KB=승인 대기 PENDING_APPROVAL).
 * - 최하단 철학 카드: 화면별 문구 (§5-1).
 *
 * 데이터 계층 컨텍스트(useAdmin)를 함께 제공한다:
 * - transport: ADMIN_UI_MODE=actual이면 계약 admin transport(HTTP + X-Demo-* 헤더),
 *   그 외에는 데모 fixture 스토어 (fixture/actual 데이터는 절대 섞지 않는다).
 * - actor: 시연 역할(OPERATOR/APPROVER) - local/private 역할 스위치일 뿐
 *   인증이 아니다 (계약 X-Demo-Role 설명). 작성자·검수자 분리(자기검수 금지)를
 *   시연하기 위해 역할별 actorId를 분리한다.
 */
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import FixtureNotice from "@/components/common/FixtureNotice";
import Logo from "@/components/common/Logo";
import {
  createAdminTransport,
  type AdminActor,
  type AdminTransport,
} from "@/lib/admin-api";
import { getFixtureAdminTransport } from "@/lib/demo-fixtures";

export type AdminUiMode = "fixture" | "actual";

const ACTORS: Record<AdminActor["role"], AdminActor> = {
  OPERATOR: { role: "OPERATOR", actorId: "OPERATOR-LOCAL-001" },
  APPROVER: { role: "APPROVER", actorId: "PM-LOCAL-001" },
};

interface AdminContextValue {
  mode: AdminUiMode;
  transport: AdminTransport;
  actor: AdminActor;
  role: AdminActor["role"];
  setRole: (role: AdminActor["role"]) => void;
  /** 상태 변경 후 사이드바 건수 뱃지 갱신 트리거 */
  notifyDataChanged: () => void;
}

const AdminContext = createContext<AdminContextValue | null>(null);

export function useAdmin(): AdminContextValue {
  const value = useContext(AdminContext);
  if (!value) throw new Error("useAdmin must be used within AdminShell");
  return value;
}

const MENU = [
  { href: "/admin", label: "운영 현황", tabLabel: "운영 현황" },
  { href: "/admin/failures", label: "실패 질문", tabLabel: "실패 질문" },
  { href: "/admin/kb-candidates", label: "KB 후보 승인", tabLabel: "KB 후보" },
];

/** §5-1 사이드바 최하단 철학 카드 - 화면별 문구 */
const PHILOSOPHY: Record<string, React.ReactNode> = {
  "/admin": (
    <>
      KPI는 기대 효과 추정치를
      <br />
      <b className="text-white">실측값으로 대체</b>하는 근거입니다.
    </>
  ),
  "/admin/failures": (
    <>
      근거 부족 실패만
      <br />
      <b className="text-white">KB 후보로 전환</b>됩니다.
    </>
  ),
  "/admin/kb-candidates": (
    <>
      AI는 제안하고,
      <br />
      <b className="text-white">판정은 담당자가 합니다.</b>
      <br />
      승인된 KB만 시민 답변에 사용돼요.
    </>
  ),
};

export default function AdminShell({
  mode,
  children,
}: Readonly<{ mode: AdminUiMode; children: React.ReactNode }>) {
  const pathname = usePathname();
  const [transport] = useState<AdminTransport>(() =>
    mode === "actual" ? createAdminTransport() : getFixtureAdminTransport(),
  );
  const [role, setRole] = useState<AdminActor["role"]>("OPERATOR");
  const actor = ACTORS[role];
  const [counts, setCounts] = useState<{ failures: number; kb: number } | null>(
    null,
  );

  // 메뉴 건수 뱃지 - 페이지 이동 시 + 페이지 내 상태 변경 이벤트 시 갱신
  const refreshCounts = useCallback(() => {
    void Promise.all([
      transport.listFailedQuestions(actor),
      transport.listCandidates(actor),
    ])
      .then(([failures, candidates]) => {
        setCounts({
          failures: failures.items.filter((f) => f.status === "NEW").length,
          kb: candidates.items.filter((c) => c.status === "PENDING_APPROVAL")
            .length,
        });
      })
      .catch(() => {
        setCounts(null);
      });
  }, [actor, transport]);

  useEffect(() => {
    if (pathname === "/admin/login") return;
    refreshCounts();
    window.addEventListener("admin:data-changed", refreshCounts);
    return () => {
      window.removeEventListener("admin:data-changed", refreshCounts);
    };
  }, [pathname, refreshCounts]);

  // 관문 화면은 셸 없이 그대로 - 단 컨텍스트는 제공한다
  const contextValue: AdminContextValue = {
    mode,
    transport,
    actor,
    role,
    setRole,
    notifyDataChanged: () => window.dispatchEvent(new Event("admin:data-changed")),
  };

  if (pathname === "/admin/login") {
    return (
      <AdminContext.Provider value={contextValue}>
        {/* fixture 모드 상시 배너 - 관문 화면 포함 전 화면 (태성 리뷰 2) */}
        {mode === "fixture" && <FixtureNotice />}
        {children}
      </AdminContext.Provider>
    );
  }

  const badgeOf = (href: string): number | null => {
    if (counts === null) return null;
    if (href === "/admin/failures") return counts.failures;
    if (href === "/admin/kb-candidates") return counts.kb;
    return null;
  };

  return (
    <AdminContext.Provider value={contextValue}>
      {/* fixture 모드 상시 배너 - 공지·사이드바와 구분되는 앰버 톤 (태성 리뷰 2) */}
      {mode === "fixture" && <FixtureNotice />}
      <div className="min-h-screen md:flex">
        {/* 768px 미만: 상단 고정 바 - 로고 줄 + 메뉴 탭 줄 (모바일 정비 1) */}
        <header className="sticky top-0 z-40 bg-admin-nav md:hidden">
          <div className="flex h-14 items-center justify-between gap-2 px-4">
            {/* 워드마크 문법(최종 폴리시 4): 흰 변형은 "이음"만 밝은 하늘색.
                로고 = 운영 현황 홈 링크 (멘토 QA, 사이드바와 동일 동작) */}
            <Link
              href="/admin"
              aria-label="이음센터 운영 현황으로"
              className="flex items-center gap-1.5 rounded-btn-s text-[17px] font-extrabold text-white"
            >
              <Logo className="h-5 w-5 shrink-0 text-white" />
              <span>
                <span className="text-tie-line">이음</span>센터
              </span>
            </Link>
            {/* 상단 바 우측 간결 드롭다운 = 시연 환경 축약형 (멘토 QA).
                현재 actor는 aria-label로 스크린리더에 알린다 */}
            <label className="sr-only" htmlFor="demo-role-mobile">
              시연 역할
            </label>
            <select
              id="demo-role-mobile"
              aria-label={`시연 역할 선택 · 현재 ${actor.actorId} · 인증 아님`}
              value={role}
              onChange={(event) => setRole(event.target.value as AdminActor["role"])}
              className="demo-role-select min-h-9 max-w-[46%] rounded-btn-s border border-white/20 bg-white/[0.07] px-2 text-[13px] font-semibold text-white"
            >
              <option value="OPERATOR" className="text-text">
                작성 운영자
              </option>
              <option value="APPROVER" className="text-text">
                별도 승인자
              </option>
            </select>
          </div>
          <nav aria-label="관리자 메뉴 (모바일)" className="bg-white/[0.07]">
            <ul className="flex h-12 overflow-x-auto px-2">
              {MENU.map((m) => {
                const active = pathname === m.href;
                const badge = badgeOf(m.href);
                return (
                  <li key={m.href} className="shrink-0">
                    <Link
                      href={m.href}
                      aria-current={active ? "page" : undefined}
                      className={`flex h-12 items-center gap-1.5 border-b-2 px-3 text-note whitespace-nowrap ${
                        active
                          ? "border-white font-extrabold text-white"
                          : "border-transparent font-semibold text-admin-nav-soft hover:text-white"
                      }`}
                    >
                      {m.tabLabel}
                      {badge !== null && badge > 0 && (
                        <span
                          className={`rounded-pill px-1.5 py-px text-[12px] font-bold tabular-nums ${
                            active
                              ? "bg-primary text-white"
                              : "bg-white/15 text-white"
                          }`}
                        >
                          {badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </header>

        {/* 사이드바 sticky 고정 (멘토 QA): 본문 스크롤 중에도 상단 고정.
            h-screen + self-start로 뷰포트 높이 고정, 내용 초과 시 내부 스크롤.
            모바일(md 미만)은 상단 바 레이아웃이라 영향 없음 */}
        <aside className="hidden w-[216px] shrink-0 flex-col gap-[22px] bg-admin-nav px-3.5 py-[22px] md:sticky md:top-0 md:flex md:h-screen md:self-start md:overflow-y-auto">
          {/* 브랜드 - 로고 심볼 흰색 변형 (§5-1). 로고 = 운영 현황 홈 링크 (멘토 QA) */}
          <div className="px-2">
            <Link
              href="/admin"
              aria-label="이음센터 운영 현황으로"
              className="block rounded-btn-s"
            >
              <span className="flex items-center gap-1.5 text-[12.5px] font-semibold text-tie-line">
                <Logo className="h-4 w-4 shrink-0 text-white" />
                세종 민원이음 관리자
              </span>
              {/* 워드마크 문법(최종 폴리시 4): 흰 변형은 "이음"만 밝은 하늘색 */}
              <p className="mt-0.5 text-[20px] font-extrabold text-white">
                <span className="text-tie-line">이음</span>센터
              </p>
            </Link>
          </div>

          <nav aria-label="관리자 메뉴">
            <ul className="flex flex-col gap-1">
              {MENU.map((m) => {
                const active = pathname === m.href;
                const badge = badgeOf(m.href);
                return (
                  <li key={m.href}>
                    <Link
                      href={m.href}
                      aria-current={active ? "page" : undefined}
                      className={`flex min-h-11 items-center justify-between gap-2 rounded-btn-s px-3 py-[11px] text-note ${
                        active
                          ? "bg-white font-extrabold text-admin-nav"
                          : "font-semibold text-admin-nav-soft hover:bg-white/[0.08] hover:text-white"
                      }`}
                    >
                      <span>{m.label}</span>
                      {badge !== null && badge > 0 && (
                        <span
                          className={`rounded-pill px-2 py-0.5 text-[12.5px] font-bold tabular-nums ${
                            active
                              ? "bg-primary text-white"
                              : "bg-white/15 text-white"
                          }`}
                        >
                          {badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* 하단 고정 그룹: 시연 환경 패널 + 철학 카드 (멘토 QA).
              흩어져 있던 시연 라벨·actor·샘플 뱃지를 단일 카드로 통합한다.
              작성자·검수자 분리(자기검수 금지) 시연은 그대로 - 기능 변경 없음 */}
          <div className="mt-auto flex flex-col gap-3.5">
            {/* 시연 환경 패널 - 메뉴와 상단 헤어라인으로 구분 */}
            <div className="border-t border-white/10 pt-3.5">
              <div className="rounded-btn bg-white/[0.07] p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[12px] font-bold text-white">
                    시연 환경
                  </span>
                  <span className="text-[11px] font-semibold text-admin-nav-soft">
                    인증 아님
                  </span>
                </div>
                {/* actor 드롭다운(네이비 테마) - 현재 actor는 시각 중복을 피해
                    aria-label로만 남긴다. 흰 배경 select 금지 */}
                <label htmlFor="demo-role" className="sr-only">
                  시연 역할 선택
                </label>
                <select
                  id="demo-role"
                  aria-label={`시연 역할 선택 · 현재 ${actor.actorId} · 인증 아님`}
                  value={role}
                  onChange={(event) =>
                    setRole(event.target.value as AdminActor["role"])
                  }
                  className="demo-role-select mt-2 min-h-11 w-full rounded-btn-s border border-white/20 bg-white/[0.07] px-2.5 text-note font-semibold text-white"
                >
                  <option value="OPERATOR" className="text-text">
                    작성 운영자 · OPERATOR-LOCAL-001
                  </option>
                  <option value="APPROVER" className="text-text">
                    별도 승인자 · PM-LOCAL-001
                  </option>
                </select>
                {/* 데이터 출처 - 버튼처럼 보이지 않게 점 아이콘 + 캡션으로 강등 */}
                <p className="mt-2.5 flex items-center gap-1.5 text-table-head font-semibold text-admin-nav-soft">
                  <span
                    aria-hidden="true"
                    className="h-1.5 w-1.5 shrink-0 rounded-full bg-admin-nav-soft"
                  />
                  {mode === "fixture"
                    ? "시연용 샘플 데이터"
                    : "실제 local DB API 연결"}
                </p>
              </div>
            </div>

            {/* 철학 카드 (§5-1) */}
            <div className="rounded-btn bg-white/[0.07] p-3 text-table-head leading-[1.5] text-admin-nav-soft">
              {PHILOSOPHY[pathname] ?? PHILOSOPHY["/admin"]}
            </div>
          </div>
        </aside>
        <div className="min-w-0 flex-1 bg-bg-admin">{children}</div>
      </div>
    </AdminContext.Provider>
  );
}
