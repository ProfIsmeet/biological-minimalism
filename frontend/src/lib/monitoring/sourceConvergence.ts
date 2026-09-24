import { sourceIdentityFromStatus, sourceIdentityKey } from "@/lib/monitoring/sourceIdentity";
import type { DataSourceStatus } from "@/lib/types";

export interface SourceConvergenceRequestPlan {
  shouldRequest: boolean;
  requestKey: string | null;
  nextLastRequestedKey: string | null;
}

/**
 * One request per observed mismatch identity. A null key resets the dedupe
 * boundary so a later, genuinely new transition back to the same identity
 * can request convergence again.
 */
export function planSourceConvergenceRequest(
  pendingKey: string | null,
  lastRequestedKey: string | null,
): SourceConvergenceRequestPlan {
  if (pendingKey === null) {
    return { shouldRequest: false, requestKey: null, nextLastRequestedKey: null };
  }
  if (pendingKey === lastRequestedKey) {
    return { shouldRequest: false, requestKey: null, nextLastRequestedKey: lastRequestedKey };
  }
  return { shouldRequest: true, requestKey: pendingKey, nextLastRequestedKey: pendingKey };
}

export function statusConfirmsSourceConvergence(status: DataSourceStatus, pendingKey: string | null): boolean {
  if (pendingKey === null) return true;
  const identity = sourceIdentityFromStatus(status);
  return identity !== null && sourceIdentityKey(identity) === pendingKey;
}

export type SourceConvergenceStatusDisposition =
  | "no_pending"
  | "unchanged_pre_convergence_authority"
  | "confirmed_pending_identity"
  | "advanced_to_third_authority";

/**
 * Classifies an authoritative REST result against the complete convergence
 * transition, not only its pending target. This makes unchanged A, confirmed
 * B, and a third authoritative C deterministic and order-independent.
 */
export function classifySourceConvergenceStatus(
  status: DataSourceStatus,
  pendingKey: string | null,
  preConvergenceAuthorityKey: string | null,
): SourceConvergenceStatusDisposition {
  if (pendingKey === null) return "no_pending";
  const identity = sourceIdentityFromStatus(status);
  const statusKey = identity ? sourceIdentityKey(identity) : null;
  if (statusKey === pendingKey) return "confirmed_pending_identity";
  if (statusKey !== null && statusKey === preConvergenceAuthorityKey) {
    return "unchanged_pre_convergence_authority";
  }
  return "advanced_to_third_authority";
}

export type SourceStateRequestOwner = string | symbol;
export type SourceStateRequestReason = "initial_seed" | "convergence" | "retry";

export interface SourceStatePhysicalRequestSnapshot {
  generation: number;
  pendingKey: string | null;
  reason: SourceStateRequestReason;
  settled: boolean;
}

export interface SourceStateRequestRegistration {
  generation: number;
  pendingKey: string | null;
  reason: SourceStateRequestReason;
  adopted: boolean;
  outcome: Promise<SourceStateRequestOutcome>;
}

export interface SourceStateMutationTicket {
  owner: SourceStateRequestOwner;
  ownerEpoch: number;
  generation: number;
}

export interface SourceStateMutationRegistration {
  ticket: SourceStateMutationTicket;
  outcome: Promise<SourceStateRequestOutcome>;
}

export interface SourceStateRequestCoordinatorSnapshot {
  active: boolean;
  owner: SourceStateRequestOwner | null;
  ownerEpoch: number;
  generation: number;
  initialRequestPlanned: boolean;
  lastRequestedPendingKey: string | null;
  inFlight: SourceStatePhysicalRequestSnapshot | null;
}

interface SourceStateRequestSettlement {
  disposition: "accepted" | "error";
  value: DataSourceStatus | unknown;
}

interface SourceStatePhysicalRequest extends SourceStatePhysicalRequestSnapshot {
  settlement: SourceStateRequestSettlement | null;
}

interface SourceStateRequestSubscriber {
  owner: SourceStateRequestOwner;
  ownerEpoch: number;
  generation: number;
  onAccepted: (result: DataSourceStatus) => void;
  onError: (error: unknown) => void;
  resolveOutcome: (outcome: SourceStateRequestOutcome) => void;
}

/**
 * Shared source-state request lifecycle for both route owners.
 *
 * The physical promise is deliberately independent of the active subscriber.
 * A replacement owner can therefore adopt the same unresolved request while
 * the old owner's local callbacks are detached. The same monotonically
 * increasing generation orders GETs and authoritative mutations, so an older
 * physical response or mutation cannot write after a newer operation starts.
 */
export class SourceStateRequestCoordinator {
  private active = false;
  private owner: SourceStateRequestOwner | null = null;
  private ownerEpoch = 0;
  private generation = 0;
  private initialRequestPlanned = false;
  private lastRequestedPendingKey: string | null = null;
  private inFlight: SourceStatePhysicalRequest | null = null;
  private subscriber: SourceStateRequestSubscriber | null = null;

  activateOwner(owner: SourceStateRequestOwner): void {
    if (this.owner === owner) {
      this.active = true;
      return;
    }
    this.owner = owner;
    this.active = true;
    this.ownerEpoch += 1;
    this.initialRequestPlanned = false;
    this.lastRequestedPendingKey = null;
    this.detachSubscriber();
  }

  releaseOwner(owner: SourceStateRequestOwner): void {
    if (this.owner !== owner) return;
    this.active = false;
    this.detachSubscriber();
  }

  isOwnerActive(owner: SourceStateRequestOwner): boolean {
    return this.active && this.owner === owner;
  }

  startOrAdoptRequest(
    owner: SourceStateRequestOwner,
    pendingKey: string | null,
    request: () => Promise<DataSourceStatus>,
    onAccepted: (result: DataSourceStatus) => void,
    onError: (error: unknown) => void,
    options: { force?: boolean } = {},
  ): SourceStateRequestRegistration | null {
    if (!this.isOwnerActive(owner)) return null;

    const force = options.force === true;
    const existingPhysicalRequest = this.inFlight;
    const matchingPhysicalRequest = existingPhysicalRequest?.pendingKey === pendingKey;
    if (existingPhysicalRequest && matchingPhysicalRequest && (!existingPhysicalRequest.settled || !force)) {
      return this.subscribe(owner, existingPhysicalRequest, onAccepted, onError, true);
    }

    let reason: SourceStateRequestReason;
    if (pendingKey === null) {
      this.lastRequestedPendingKey = null;
      if (this.initialRequestPlanned && !force) return null;
      this.initialRequestPlanned = true;
      reason = force ? "retry" : "initial_seed";
    } else {
      const plan = planSourceConvergenceRequest(pendingKey, this.lastRequestedPendingKey);
      if (!plan.shouldRequest && !force) return null;
      this.initialRequestPlanned = true;
      this.lastRequestedPendingKey = plan.nextLastRequestedKey;
      reason = force ? "retry" : "convergence";
    }

    this.supersedePhysicalRequest();
    this.generation += 1;
    const physicalRequest: SourceStatePhysicalRequest = {
      generation: this.generation,
      pendingKey,
      reason,
      settled: false,
      settlement: null,
    };
    this.inFlight = physicalRequest;
    const registration = this.subscribe(owner, physicalRequest, onAccepted, onError, false);

    let requestPromise: Promise<DataSourceStatus>;
    try {
      requestPromise = request();
    } catch (error) {
      requestPromise = Promise.reject(error);
    }
    void requestPromise.then(
      (result) => this.settlePhysicalRequest(physicalRequest.generation, { disposition: "accepted", value: result }),
      (error: unknown) => this.settlePhysicalRequest(physicalRequest.generation, { disposition: "error", value: error }),
    );
    return registration;
  }

  /**
   * Starts a newer authoritative mutation generation and invalidates any
   * older GET before that mutation can write. The returned ticket is scoped
   * to the active owner epoch, so unmounts and route-owner transfers make it
   * stale without relying on request cancellation.
   */
  beginAuthoritativeMutation(owner: SourceStateRequestOwner): SourceStateMutationTicket | null {
    if (!this.isOwnerActive(owner)) return null;
    this.supersedePhysicalRequest();
    this.generation += 1;
    return {
      owner,
      ownerEpoch: this.ownerEpoch,
      generation: this.generation,
    };
  }

  isAuthoritativeMutationCurrent(ticket: SourceStateMutationTicket): boolean {
    return this.active
      && this.owner === ticket.owner
      && this.ownerEpoch === ticket.ownerEpoch
      && this.generation === ticket.generation;
  }

  acceptAuthoritativeMutation(
    ticket: SourceStateMutationTicket,
    result: DataSourceStatus,
    onAccepted: (result: DataSourceStatus) => void,
  ): SourceStateRequestOutcome {
    if (!this.isAuthoritativeMutationCurrent(ticket)) return "stale";
    onAccepted(result);
    return "accepted";
  }

  rejectAuthoritativeMutation(
    ticket: SourceStateMutationTicket,
    error: unknown,
    onError: (error: unknown) => void,
  ): SourceStateRequestOutcome {
    if (!this.isAuthoritativeMutationCurrent(ticket)) return "stale";
    onError(error);
    return "error";
  }

  startAuthoritativeMutation(
    owner: SourceStateRequestOwner,
    operation: () => Promise<DataSourceStatus>,
    onAccepted: (result: DataSourceStatus) => void,
    onError: (error: unknown) => void,
  ): SourceStateMutationRegistration | null {
    const ticket = this.beginAuthoritativeMutation(owner);
    if (!ticket) return null;

    let operationPromise: Promise<DataSourceStatus>;
    try {
      operationPromise = operation();
    } catch (error) {
      operationPromise = Promise.reject(error);
    }
    const outcome = operationPromise.then(
      (result) => this.acceptAuthoritativeMutation(ticket, result, onAccepted),
      (error: unknown) => this.rejectAuthoritativeMutation(ticket, error, onError),
    );
    return { ticket, outcome };
  }

  /** Invalidates an older fetch before another authoritative operation writes. */
  supersedeOwnerRequest(owner: SourceStateRequestOwner): void {
    if (this.isOwnerActive(owner)) this.supersedePhysicalRequest();
  }

  snapshot(): SourceStateRequestCoordinatorSnapshot {
    return {
      active: this.active,
      owner: this.owner,
      ownerEpoch: this.ownerEpoch,
      generation: this.generation,
      initialRequestPlanned: this.initialRequestPlanned,
      lastRequestedPendingKey: this.lastRequestedPendingKey,
      inFlight: this.inFlight
        ? {
            generation: this.inFlight.generation,
            pendingKey: this.inFlight.pendingKey,
            reason: this.inFlight.reason,
            settled: this.inFlight.settled,
          }
        : null,
    };
  }

  private subscribe(
    owner: SourceStateRequestOwner,
    physicalRequest: SourceStatePhysicalRequest,
    onAccepted: (result: DataSourceStatus) => void,
    onError: (error: unknown) => void,
    adopted: boolean,
  ): SourceStateRequestRegistration {
    this.detachSubscriber();
    this.initialRequestPlanned = true;
    this.lastRequestedPendingKey = physicalRequest.pendingKey;
    let resolveOutcome!: (outcome: SourceStateRequestOutcome) => void;
    const outcome = new Promise<SourceStateRequestOutcome>((resolve) => {
      resolveOutcome = resolve;
    });
    this.subscriber = {
      owner,
      ownerEpoch: this.ownerEpoch,
      generation: physicalRequest.generation,
      onAccepted,
      onError,
      resolveOutcome,
    };
    if (physicalRequest.settlement) {
      void Promise.resolve().then(() => {
        if (physicalRequest.settlement) {
          this.deliverSettlement(physicalRequest, physicalRequest.settlement);
        }
      });
    }
    return {
      generation: physicalRequest.generation,
      pendingKey: physicalRequest.pendingKey,
      reason: physicalRequest.reason,
      adopted,
      outcome,
    };
  }

  private detachSubscriber(): void {
    this.subscriber?.resolveOutcome("stale");
    this.subscriber = null;
  }

  private supersedePhysicalRequest(): void {
    this.detachSubscriber();
    this.inFlight = null;
  }

  private settlePhysicalRequest(generation: number, settlement: SourceStateRequestSettlement): void {
    const physicalRequest = this.inFlight;
    if (!physicalRequest || physicalRequest.generation !== generation) return;
    physicalRequest.settled = true;
    physicalRequest.settlement = settlement;
    this.deliverSettlement(physicalRequest, settlement);
  }

  private deliverSettlement(
    physicalRequest: SourceStatePhysicalRequest,
    settlement: SourceStateRequestSettlement,
  ): void {
    const subscriber = this.subscriber;
    if (
      !subscriber
      || !this.active
      || subscriber.owner !== this.owner
      || subscriber.ownerEpoch !== this.ownerEpoch
      || subscriber.generation !== physicalRequest.generation
      || this.inFlight?.generation !== physicalRequest.generation
    ) {
      return;
    }

    this.subscriber = null;
    this.inFlight = null;
    if (settlement.disposition === "accepted") {
      subscriber.onAccepted(settlement.value as DataSourceStatus);
      subscriber.resolveOutcome("accepted");
    } else {
      subscriber.onError(settlement.value);
      subscriber.resolveOutcome("error");
    }
  }
}

export type SourceStateRequestOutcome = "accepted" | "error" | "stale";

/** One coordinator instance arbitrates ownership across full and legacy routes. */
export const sourceStateRequestCoordinator = new SourceStateRequestCoordinator();
