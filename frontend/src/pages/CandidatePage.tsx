import { type FormEvent, type ReactNode, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { ReferenceInnerPage, ReferenceNotice } from '../components/ReferenceInnerPage';
import { CandidateApiError, submitCandidateApplication } from '../candidate/candidateApi';
import { candidateFormEnabled } from '../candidate/candidateConfig';

const FIELD_CLASS =
  'w-full rounded-[5px] border border-brand-reference-line/75 bg-brand-reference-panelDeep px-4 py-3 text-base text-brand-reference-text outline-none transition shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)] focus:border-brand-reference-white focus:ring-1 focus:ring-brand-reference-white/20 disabled:cursor-not-allowed disabled:opacity-55';
const TEXTAREA_CLASS = `${FIELD_CLASS} min-h-36 resize-y`;
const HELP_CLASS = 'text-sm font-light leading-6 text-brand-reference-muted/70';
const FIELDSET_CLASS =
  'rounded-[6px] border border-brand-reference-line/30 bg-brand-reference-panel px-4 py-6 shadow-referenceCard sm:px-6 lg:px-8 lg:py-8';
const LEGEND_CLASS =
  'px-2 font-referenceHeading text-[clamp(1.65rem,3vw,2.2rem)] font-normal text-brand-reference-text';
const STATUS_NEUTRAL_CLASS = 'border-brand-reference-line/35 bg-brand-reference-panelDeep text-brand-reference-muted';
const STATUS_ERROR_CLASS = 'border-brand-reference-red/55 bg-brand-reference-red/5 text-brand-reference-text';
const STATUS_SUCCESS_CLASS = 'border-brand-reference-red/55 bg-brand-reference-red/10 text-brand-reference-text shadow-referenceCard';
const INACTIVE_COPY = 'Приём заявок через сайт временно недоступен.';
const ACTIVE_COPY = 'Форма предназначена для отправки анкеты и фотографии в ДЛ «Астрея» №3. Фотография обрабатывается приватно и не публикуется.';
const SUCCESS_COPY = 'Заявка принята. Благодарим за обращение.';
const NETWORK_COPY = 'Не удалось отправить заявку. Проверьте соединение и попробуйте ещё раз.';
const VALIDATION_COPY = 'Проверьте заполнение анкеты и выбранную фотографию.';
const TOO_LARGE_COPY = 'Файл или запрос слишком большой.';
const TOO_MANY_COPY = 'Слишком много попыток отправки. Попробуйте позже.';
const TEMPORARY_COPY = 'Отправка заявки временно недоступна. Попробуйте позже.';
const UNAVAILABLE_COPY = 'Отправка заявок временно недоступна.';
const ST_PETERSBURG_COPY = 'Я понимаю, что подаю заявку на вступление в ложу, работающую в Санкт-Петербурге';

export function CandidatePage() {
  const formLock = useRef(false);
  const feedbackRef = useRef<HTMLDivElement>(null);
  const [submissionState, setSubmissionState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [feedback, setFeedback] = useState<string | null>(null);
  const active = candidateFormEnabled;
  const submitted = submissionState === 'success';
  const disabled = !active || submissionState === 'submitting' || submitted;
  const heroLead = active ? ACTIVE_COPY : INACTIVE_COPY;

  useEffect(() => {
    if (submissionState !== 'success') {
      return;
    }

    feedbackRef.current?.focus({ preventScroll: true });
    feedbackRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [submissionState]);

  function clearFeedback() {
    if (submissionState === 'error') {
      setSubmissionState('idle');
      setFeedback(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active || formLock.current || submitted) {
      return;
    }

    const form = event.currentTarget;
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    formLock.current = true;
    setSubmissionState('submitting');
    setFeedback('Отправка…');

    try {
      const response = await submitCandidateApplication(new FormData(form));
      if (!response.accepted) {
        throw new CandidateApiError(503);
      }
      form.reset();
      setSubmissionState('success');
      setFeedback(SUCCESS_COPY);
    } catch (error) {
      setSubmissionState('error');
      setFeedback(formatCandidateSubmissionError(error));
    } finally {
      formLock.current = false;
    }
  }

  return (
    <ReferenceInnerPage eyebrow="Кандидату" title="Вступление" lead={heroLead}>
      <div className="mx-auto w-full max-w-5xl space-y-6 sm:space-y-8">
        <ReferenceNotice title={active ? 'Подача заявки' : 'Приём заявок'}>
          {active ? ACTIVE_COPY : INACTIVE_COPY}
        </ReferenceNotice>

        <form className="space-y-6 sm:space-y-8" onInput={clearFeedback} onSubmit={handleSubmit}>
          <div className="absolute left-[-10000px] top-auto h-px w-px overflow-hidden">
            <label htmlFor="website" className="sr-only">
              Website
            </label>
            <input
              id="website"
              name="website"
              type="text"
              autoComplete="off"
              tabIndex={-1}
              disabled={disabled}
              aria-hidden="true"
              className={FIELD_CLASS}
            />
          </div>

          <fieldset disabled={disabled} className={FIELDSET_CLASS}>
            <legend className={LEGEND_CLASS}>Анкета кандидата</legend>
            <div className="mt-5 grid gap-5 sm:mt-7 sm:gap-6 lg:grid-cols-2">
              <FormField id="full_name" label="Фамилия, имя, отчество" required className="lg:col-span-2">
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  required
                  maxLength={255}
                  autoComplete="name"
                  className={FIELD_CLASS}
                />
              </FormField>

              <FormField id="date_of_birth" label="Дата рождения" required>
                <input id="date_of_birth" name="date_of_birth" type="date" required className={FIELD_CLASS} />
              </FormField>

              <FormField id="city" label="Город проживания" required>
                <input
                  id="city"
                  name="city"
                  type="text"
                  required
                  maxLength={120}
                  autoComplete="address-level2"
                  className={FIELD_CLASS}
                />
              </FormField>

              <FormField id="phone" label="Телефон" required>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  required
                  maxLength={80}
                  autoComplete="tel"
                  className={FIELD_CLASS}
                />
              </FormField>

              <FormField id="email" label="Email" required>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  maxLength={255}
                  autoComplete="email"
                  className={FIELD_CLASS}
                />
              </FormField>

              <FormField id="education" label="Образование" required className="lg:col-span-2">
                <textarea id="education" name="education" required maxLength={4000} rows={4} className={TEXTAREA_CLASS} />
              </FormField>

              <FormField id="occupation" label="Работа / род занятий" required className="lg:col-span-2">
                <textarea id="occupation" name="occupation" required maxLength={4000} rows={4} className={TEXTAREA_CLASS} />
              </FormField>

              <FormField id="marital_status" label="Семейное положение" required>
                <input
                  id="marital_status"
                  name="marital_status"
                  type="text"
                  required
                  maxLength={120}
                  className={FIELD_CLASS}
                />
              </FormField>

              <div className="lg:col-span-2">
                <div className="rounded-[5px] border border-brand-reference-red/35 bg-brand-reference-red/5 px-4 py-4 sm:px-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-reference-red">Предупреждение</p>
                  <p className="mt-2 text-sm font-light leading-6 text-brand-reference-muted">
                    Не указывайте сведения о политических взглядах, религиозных или философских убеждениях,
                    состоянии здоровья и иных специальных категориях персональных данных.
                  </p>
                </div>
              </div>

              <FormField id="other_organizations" label="Членство в иных организациях" className="lg:col-span-2">
                <textarea id="other_organizations" name="other_organizations" maxLength={4000} rows={4} className={TEXTAREA_CLASS} />
              </FormField>

              <FormField id="social_links" label="VK / публичные социальные ссылки" className="lg:col-span-2">
                <textarea id="social_links" name="social_links" maxLength={4000} rows={4} className={TEXTAREA_CLASS} />
              </FormField>

              <FormField id="motivation" label="О себе / мотивация" required className="lg:col-span-2">
                <textarea id="motivation" name="motivation" required maxLength={4000} rows={7} className={TEXTAREA_CLASS} />
              </FormField>
            </div>
          </fieldset>

          <fieldset disabled={disabled} className={FIELDSET_CLASS}>
            <legend className={LEGEND_CLASS}>Фотография</legend>
            <div className="mt-5 grid gap-4 sm:mt-7">
              <div className="grid gap-2">
                <label htmlFor="photo" className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-reference-muted">
                  Фотография<span aria-hidden="true" className="text-brand-reference-red"> *</span>
                </label>
                <input
                  id="photo"
                  name="photo"
                  type="file"
                  required
                  accept="image/jpeg,image/png,image/webp"
                  className={`${FIELD_CLASS} py-2`}
                />
              </div>
              <p className={HELP_CLASS}>JPG, PNG или WebP. Фотография обрабатывается приватно и не публикуется.</p>
            </div>
          </fieldset>

          <fieldset disabled={disabled} className={FIELDSET_CLASS}>
            <legend className={LEGEND_CLASS}>Согласия</legend>
            <div className="mt-5 space-y-3 sm:mt-7 sm:space-y-4">
              <ConsentRow id="personal_data_processing" name="personal_data_processing">
                <span>
                  <Link
                    to="/consent"
                    className="text-brand-reference-text underline decoration-brand-reference-red/60 underline-offset-3 transition-colors hover:text-white"
                  >
                    Согласен(на) на обработку персональных данных
                  </Link>
                </span>
              </ConsentRow>

              <ConsentRow id="privacy_policy_acknowledgement" name="privacy_policy_acknowledgement">
                <span>
                  <Link
                    to="/privacy"
                    className="text-brand-reference-text underline decoration-brand-reference-red/60 underline-offset-3 transition-colors hover:text-white"
                  >
                    Ознакомлен(а) с политикой конфиденциальности
                  </Link>
                </span>
              </ConsentRow>

              <ConsentRow id="saint_petersburg_acknowledgement" name="saint_petersburg_acknowledgement">
                {ST_PETERSBURG_COPY}
              </ConsentRow>
            </div>
          </fieldset>

          <div className={FIELDSET_CLASS}>
            <div
              ref={feedbackRef}
              role={submissionState === 'error' ? 'alert' : 'status'}
              aria-live="polite"
              tabIndex={-1}
              className={`rounded-[5px] border px-4 py-4 text-sm font-light leading-6 outline-none focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-reference-red sm:px-5 ${
                submissionState === 'error'
                  ? STATUS_ERROR_CLASS
                  : submissionState === 'success'
                    ? `px-5 py-5 ${STATUS_SUCCESS_CLASS}`
                    : STATUS_NEUTRAL_CLASS
              }`}
            >
              {submissionState === 'success' ? (
                <p className="mb-3 font-referenceHeading text-2xl text-brand-reference-text">Заявка успешно отправлена</p>
              ) : null}
              {feedback ?? (active ? 'Заполните все поля, прикрепите фотографию и отметьте все три согласия.' : INACTIVE_COPY)}
            </div>

            <div className="mt-5 flex flex-col gap-4 sm:mt-6 md:flex-row md:items-center md:justify-between">
              <p className={HELP_CLASS}>
                Перед отправкой проверьте данные, фотографию и все три согласия. Во время отправки повторное нажатие будет недоступно.
              </p>
              <button
                type="submit"
                disabled={disabled}
                className="inline-flex w-full shrink-0 items-center justify-center rounded-[5px] border border-brand-reference-red bg-brand-reference-red px-5 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-white transition hover:bg-transparent hover:text-brand-reference-text focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-reference-red disabled:cursor-not-allowed disabled:opacity-45 md:w-auto md:max-w-[270px]"
              >
                {submissionState === 'submitting'
                  ? 'Отправка…'
                  : submitted
                    ? 'Заявка отправлена'
                    : active
                      ? 'Отправить заявку'
                      : 'Приём заявок временно недоступен'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </ReferenceInnerPage>
  );
}

type FormFieldProps = {
  id: string;
  label: string;
  required?: boolean;
  help?: string;
  className?: string;
  children: ReactNode;
};

function FormField({ id, label, required = false, help, className = '', children }: FormFieldProps) {
  return (
    <div className={`grid gap-2 ${className}`}>
      <label htmlFor={id} className="text-xs font-semibold uppercase tracking-[0.12em] text-brand-reference-muted">
        {label}
        {required ? <span aria-hidden="true" className="text-brand-reference-red"> *</span> : null}
      </label>
      {children}
      {help ? <p className={HELP_CLASS}>{help}</p> : null}
    </div>
  );
}

type ConsentRowProps = {
  id: string;
  name: string;
  children: ReactNode;
};

function ConsentRow({ id, name, children }: ConsentRowProps) {
  return (
    <div className="flex gap-3 rounded-[5px] border border-brand-reference-line/25 bg-brand-reference-panelDeep px-4 py-4">
      <input
        id={id}
        name={name}
        type="checkbox"
        value="true"
        required
        className="mt-1 h-4 w-4 shrink-0 accent-brand-reference-red"
      />
      <label htmlFor={id} className="text-sm font-light leading-6 text-brand-reference-muted">
        {children}
      </label>
    </div>
  );
}

function formatCandidateSubmissionError(error: unknown): string {
  if (error instanceof CandidateApiError) {
    switch (error.status) {
      case 400:
      case 422:
        return VALIDATION_COPY;
      case 404:
        return UNAVAILABLE_COPY;
      case 413:
        return TOO_LARGE_COPY;
      case 429:
        return TOO_MANY_COPY;
      case 503:
        return TEMPORARY_COPY;
      default:
        return TEMPORARY_COPY;
    }
  }

  return NETWORK_COPY;
}
